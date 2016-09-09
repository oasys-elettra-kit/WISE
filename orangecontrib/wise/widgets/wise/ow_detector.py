import numpy
import time
from PyQt4.QtGui import QApplication, QPalette, QColor, QFont, QMessageBox, QFileDialog, QSlider
from PyQt4.QtCore import QRect, Qt
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from orangecontrib.wise.util.wise_objects import WiseOutput
from orangecontrib.wise.widgets.gui.ow_wise_widget import WiseWidget
from orangecontrib.wise.util.wise_propagator import WisePropagatorsChain, WisePropagationAlgorithms, WisePropagationParameters

from  wiselib.Rayman5 import Amp

class OWDetector(WiseWidget):
    name = "Detector"
    id = "Detector"
    description = "Detector"
    icon = "icons/detector.png"
    priority = 3
    category = ""
    keywords = ["wise", "elliptical"]

    inputs = [("Input", WiseOutput, "set_input")]
    outputs = []

    detector_size = 0.0
    oe_f2 = 0.0
    defocus_sweep = Setting(0.0)
    defocus_start = Setting(-10e-3)
    defocus_stop = Setting(10e-3)
    defocus_step = Setting(1e-3)
    use_multipool = Setting(0)
    n_pools = Setting(5)
    show_animation = Setting(0)

    input_data = None


    def set_input(self, input_data):
        self.setStatusMessage("")

        if not input_data is None:
            if not input_data.has_optical_element():
                QMessageBox.critical(self, "Error", "Detector can be collegated only after an Optical Element", QMessageBox.Ok)

                self.setStatusMessage("Error!")

            self.input_data = input_data

            optical_element = self.input_data.get_optical_element()

            self.detector_size = numpy.round(optical_element.get_property("detector_size")*1e6, 1)
            self.oe_f2         = optical_element.inner_wise_optical_element.f2/self.workspace_units_to_m

            self.compute()


    def build_gui(self):
        self.view_type = 1
        self.button_box.setVisible(False)

        main_box = oasysgui.widgetBox(self.controlArea, "Detector Parameters", orientation="vertical", width=self.CONTROL_AREA_WIDTH-5)

        le_detector_size = oasysgui.lineEdit(main_box, self, "detector_size", "detector_size [" + u"\u03BC" + "m]", labelWidth=260, valueType=float, orientation="horizontal")
        le_detector_size.setReadOnly(True)
        font = QFont(le_detector_size.font())
        font.setBold(True)
        le_detector_size.setFont(font)
        palette = QPalette(le_detector_size.palette())
        palette.setColor(QPalette.Text, QColor('dark blue'))
        palette.setColor(QPalette.Base, QColor(243, 240, 160))
        le_detector_size.setPalette(palette)

        self.le_oe_f2 = oasysgui.lineEdit(main_box, self, "oe_f2", "O.E. F2", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_oe_f2.setReadOnly(True)
        font = QFont(self.le_oe_f2.font())
        font.setBold(True)
        self.le_oe_f2.setFont(font)
        palette = QPalette(self.le_oe_f2.palette())
        palette.setColor(QPalette.Text, QColor('dark blue'))
        palette.setColor(QPalette.Base, QColor(243, 240, 160))
        self.le_oe_f2.setPalette(palette)

        self.le_defocus_sweep = oasysgui.lineEdit(main_box, self, "defocus_sweep", "Defocus sweep", labelWidth=260, valueType=float, orientation="horizontal")

        gui.button(main_box, self, "Move Detector on Defocused Position", callback=self.compute, height=35)

        best_focus_box = oasysgui.widgetBox(self.controlArea, "Best Focus Calculation", orientation="vertical", width=self.CONTROL_AREA_WIDTH-5)

        self.le_defocus_start = oasysgui.lineEdit(best_focus_box, self, "defocus_start", "Defocus sweep start", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_defocus_stop  = oasysgui.lineEdit(best_focus_box, self, "defocus_stop", "Defocus sweep stop", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_defocus_step  = oasysgui.lineEdit(best_focus_box, self, "defocus_step", "Defocus sweep step", labelWidth=260, valueType=float, orientation="horizontal")

        gui.comboBox(best_focus_box, self, "use_multipool", label="Use Parallel Processing",
                     items=["No", "Yes"], labelWidth=260,
                     callback=self.set_Multipool, sendSelectedValue=False, orientation="horizontal")

        self.use_multipool_box = oasysgui.widgetBox(best_focus_box, "", addSpace=True, orientation="vertical", height=30)
        self.use_multipool_box_empty = oasysgui.widgetBox(best_focus_box, "", addSpace=True, orientation="vertical", height=30)

        oasysgui.lineEdit(self.use_multipool_box, self, "n_pools", "Nr. Parallel Processes", labelWidth=260, valueType=int, orientation="horizontal")

        self.set_Multipool()

        gui.separator(best_focus_box, height=5)

        gui.checkBox(best_focus_box, self, "show_animation", "Show animation during calculation")

        gui.separator(best_focus_box, height=5)

        gui.button(best_focus_box, self, "Find Best Focus Position", callback=self.do_best_focus_calculation, height=35)
        self.save_button = gui.button(best_focus_box, self, "Save Best Focus Calculation Complete Results", callback=self.save_best_focus_results, height=35)
        self.save_button.setEnabled(False)

        self.best_focus_slider = None

    def set_Multipool(self):
        self.use_multipool_box.setVisible(self.use_multipool == 1)
        self.use_multipool_box_empty.setVisible(self.use_multipool == 0)

    def set_ViewType(self):
        self.view_type = 1

    def after_change_workspace_units(self):
        label = self.le_oe_f2.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_defocus_sweep.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_defocus_start.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_defocus_stop.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_defocus_step.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")


    def check_fields(self):
        if self.use_multipool == 1:
            self.n_pools = congruence.checkStrictlyPositiveNumber(self.n_pools, "Nr. Parallel Processes")

    def do_wise_calculation(self):
        if self.input_data is None:
            raise Exception("No Input Data!")

        if self.defocus_sweep == 0.0:
            wavefront = self.input_data.get_wavefront()

            data_to_plot = numpy.zeros((2, len(wavefront.positions)))
            data_to_plot[0, :] = wavefront.positions * 1e6
            data_to_plot[1, :] = Amp(wavefront.electric_fields)**2
        else:
            if self.oe_f2 + self.defocus_sweep <= 0: raise Exception("Defocus sweep reached the previous mirror")


            propagation_parameter = WisePropagationParameters(source=self.input_data.get_source().inner_wise_source,
                                                              optical_element=self.input_data.get_optical_element().inner_wise_optical_element,
                                                              detector_size=self.input_data.get_optical_element().get_property("detector_size"),
                                                              defocus_sweep=self.defocus_sweep * self.workspace_units_to_m)


            propagation_output = WisePropagatorsChain.Instance().do_propagation(propagation_parameter,
                                                                                WisePropagationAlgorithms.HuygensIntegral)


            positions = propagation_output.det_s
            electric_fields = propagation_output.electric_fields

            data_to_plot = numpy.zeros((5, len(positions)))
            data_to_plot[0, :] = positions * 1e6
            data_to_plot[1, :] = Amp(electric_fields)**2

        return data_to_plot

    def getTabTitles(self):
        return ["Intensity on O.E. Focus", "Intensity on Best Focus"]

    def getTitles(self):
        return ["Intensity on Focus Position: " + str(numpy.round(self.oe_f2 + self.defocus_sweep, 6))]

    def getXTitles(self):
        return ["Z [$\mu$m]"]

    def getYTitles(self):
        return ["Intensity"]

    def getVariablesToPlot(self):
        return [(0, 1)]

    def getLogPlot(self):
        return [(False, False)]

    def extract_plot_data_from_calculation_output(self, calculation_output):
        return calculation_output

    def extract_wise_output_from_calculation_output(self, calculation_output):
        return None

    def do_best_focus_calculation(self):
        try:
            if self.input_data is None:
                raise Exception("No Input Data!")

            if self.defocus_start >= self.defocus_stop: raise Exception("Defocus sweep start must be < Defocus sweep stop")
            self.defocus_step = congruence.checkStrictlyPositiveNumber(self. defocus_step, "Defocus sweep step")
            if self.defocus_step >= self.defocus_stop - self.defocus_start: raise Exception("Defocus step is too big")

            if self.best_focus_slider is None:
                self.best_focus_slider = QSlider(self.tab[1])
                self.best_focus_slider.setGeometry(QRect(0, 0, 320, 50))
                self.best_focus_slider.setOrientation(Qt.Horizontal)
                self.best_focus_slider.setInvertedAppearance(False)
                self.best_focus_slider.setInvertedControls(False)

                self.tab[1].layout().addWidget(self.best_focus_slider)
            else:
                self.best_focus_slider.valueChanged.disconnect()


            self.setStatusMessage("")
            self.progressBarInit()

            source =  self.input_data.get_source().inner_wise_source
            elliptic_mirror = self.input_data.get_optical_element().inner_wise_optical_element
            detector_size = self.input_data.get_optical_element().get_property("detector_size")

            self.defocus_list = numpy.arange(self.defocus_start * self.workspace_units_to_m,
                                             self.defocus_stop  * self.workspace_units_to_m,
                                             self.defocus_step  * self.workspace_units_to_m)

            n_defocus = len(self.defocus_list)

            if self.defocus_list[-1] != self.defocus_stop  * self.workspace_units_to_m:
                n_defocus += 1
                self.defocus_list.resize(n_defocus)
                self.defocus_list[-1] = self.defocus_stop  * self.workspace_units_to_m

            self.best_focus_slider.setTickInterval(1)
            self.best_focus_slider.setSingleStep(1)
            self.best_focus_slider.setMinimum(0)
            self.best_focus_slider.setMaximum(n_defocus-1)
            self.best_focus_slider.setValue(0)

            progress_bar_increment = 100/n_defocus

            if self.use_multipool == 0:
                n_pools = 0
            else:
                n_pools = self.n_pools

            index_min = -1
            hew_min = numpy.inf

            self.best_focus_index = -1
            self.electric_fields_list = []
            self.positions_list = []
            self.hews_list = []

            propagation_parameter = WisePropagationParameters(source=source,
                                                              optical_element=elliptic_mirror,
                                                              detector_size=detector_size,
                                                              n_pools=n_pools)


            self.setStatusMessage("Calculating Best Focus Position")

            if self.show_animation == 1: time.sleep(0.5)

            for i, defocus in enumerate(self.defocus_list):
                if numpy.abs(defocus) < 1e-15:
                    defocus = 0.0
                    self.defocus_list[i] = 0.0


                propagation_parameter.defocus_sweep = defocus

                propagation_output = WisePropagatorsChain.Instance().do_propagation(propagation_parameter,
                                                                                    WisePropagationAlgorithms.HuygensIntegral)
                # E1
                self.electric_fields_list.append(propagation_output.electric_fields)
                self.positions_list.append(propagation_output.det_s)
                self.hews_list.append(propagation_output.HEW)

                self.best_focus_slider.setValue(i)

                if self.show_animation == 1:
                    self.plot_histo(propagation_output.det_s * 1e6,
                                    Amp(propagation_output.electric_fields)**2,
                                    i*progress_bar_increment,
                                    tabs_canvas_index=1,
                                    plot_canvas_index=1,
                                    title="Defocus Sweep: " + str(defocus/self.workspace_units_to_m) + " (" + str(i+1) + "/" + str(n_defocus) + "), HEW: " + str(round(propagation_output.HEW, 5)),
                                    xtitle="Z [$\mu$m]",
                                    ytitle="Intensity",
                                    log_x=False,
                                    log_y=False)

                    time.sleep(0.1)

                    self.tabs.setCurrentIndex(1)
                else:
                    self.progressBarSet(value=i*progress_bar_increment)

                if propagation_output.HEW < hew_min:
                    hew_min = propagation_output.HEW
                    index_min = i

            self.best_focus_index = index_min
            best_focus_electric_fields = self.electric_fields_list[index_min]
            best_focus_positions       = self.positions_list[index_min]

            if self.show_animation == 1:
                QMessageBox.information(self,
                                        "Best Focus Calculation",
                                        "Best Focus Found!\n\nPosition: " + str(self.oe_f2 + (self.defocus_list[index_min]/self.workspace_units_to_m)) + "\nHEW: " + str(round(self.hews_list[index_min], 5)),
                                        QMessageBox.Ok
                                        )

            self.plot_histo(best_focus_positions * 1e6,
                            Amp(best_focus_electric_fields) ** 2,
                            100,
                            tabs_canvas_index=1,
                            plot_canvas_index=1,
                            title="(BEST FOCUS) Defocus Sweep: " + str(self.defocus_list[index_min]/self.workspace_units_to_m) + " ("+ str(index_min+1) + "/" + str(n_defocus) + "), Position: " + str(self.oe_f2 + (self.defocus_list[index_min]/self.workspace_units_to_m)) + ", HEW: " + str(round(self.hews_list[index_min], 5)),
                            xtitle="Z [$\mu$m]",
                            ytitle="Intensity",
                            log_x=False,
                            log_y=False)

            self.best_focus_slider.setValue(index_min)
            self.best_focus_slider.valueChanged.connect(self.plot_detail)

            self.tabs.setCurrentIndex(1)
            self.setStatusMessage("")

            self.save_button.setEnabled(True)

        except Exception as exception:
            QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

            self.setStatusMessage("Error!")

            #raise exception

        self.progressBarFinished()


    def plot_detail(self, value):
        try:
            index = value
            n_defocus = len(self.positions_list)

            electric_fields = self.electric_fields_list[index]
            positions       = self.positions_list[index]

            if index == self.best_focus_index:
                title = "(BEST FOCUS) Defocus Sweep: " + str(self.defocus_list[index]/self.workspace_units_to_m) + " ("+ str(index+1) + "/" + str(n_defocus) + "), Position: " + str(self.oe_f2 + (self.defocus_list[index]/self.workspace_units_to_m)) + ", HEW: " + str(round(self.hews_list[index], 5))
            else:
                title = "Defocus Sweep: " + str(self.defocus_list[index]/self.workspace_units_to_m) + " (" + str(index+1) + "/" + str(n_defocus) + "), HEW: " + str(round(self.hews_list[index], 5))


            self.plot_histo(positions * 1e6,
                            Amp(electric_fields)**2,
                            100,
                            tabs_canvas_index=1,
                            plot_canvas_index=1,
                            title=title,
                            xtitle="Z [$\mu$m]",
                            ytitle="Intensity",
                            log_x=False,
                            log_y=False)


            self.tabs.setCurrentIndex(1)
        except:
            pass

    def save_best_focus_results(self):
        try:
            path_dir = QFileDialog.getExistingDirectory(self, "Select destination directory", ".", QFileDialog.ShowDirsOnly)

            if not path_dir is None:
                if not path_dir.strip() == "":
                    if QMessageBox.question(self,
                                            "Save Data",
                                            "Data will be saved in :\n\n" + path_dir + "\n\nConfirm?",
                                            QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                        for index in range(0, len(self.electric_fields_list)):
                            file_name = "best_focus_partial_result_" + str(index) + ".dat"

                            file = open(path_dir + "/" + file_name, "w")

                            intensities = Amp(self.electric_fields_list[index]) ** 2

                            file.write("# Defocus Sweep: " + str(self.defocus_list[index]) + " [m] \n")
                            file.write("# HEW          : " + str(self.hews_list[index]) + "\n")
                            file.write("# Position [m]  Intensity\n")

                            for i in range (0, len(self.positions_list[index])):
                                file.write(str(self.positions_list[index][i]) + " " + str(intensities[i]) + "\n")


                            file.close()

                        QMessageBox.information(self,
                                                "Best Focus Calculation",
                                                "Best Focus Calculation complete results saved on directory:\n\n" + path_dir,
                                                QMessageBox.Ok
                                                )

        except Exception as exception:
            QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

            self.setStatusMessage("Error!")
