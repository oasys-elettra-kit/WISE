import sys
import numpy
from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QSlider
from PyQt5.QtCore import QRect, Qt
from orangewidget import gui
from orangewidget.widget import OWAction
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.util.oasys_util import EmittingStream

from orangecontrib.wise.util.wise_objects import WiseOutput, WiseNumericalIntegrationParameters
from orangecontrib.wise.widgets.gui.ow_wise_widget import WiseWidget
from orangecontrib.wise.util.wise_propagator import WisePropagatorsChain, WisePropagationAlgorithms, WisePropagationParameters

from  wiselib.Rayman import Amp

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

    calculation_type = Setting(0)
    number_of_points = Setting(0)
    detector_size = Setting(50)
    calculated_number_of_points = 0
    oe_f2 = 0.0
    defocus_sweep = Setting(0.0)
    defocus_start = Setting(-1.0)
    defocus_stop = Setting(1.0)
    defocus_step = Setting(0.1)
    use_multipool = Setting(0)
    n_pools = Setting(5)
    show_animation = Setting(0)

    input_data = None
    run_calculation = True

    def set_input(self, input_data):
        self.setStatusMessage("")

        if not input_data is None:
            if not input_data.has_optical_element():
                QMessageBox.critical(self, "Error", "Detector can be collegated only after an Optical Element", QMessageBox.Ok)

                self.setStatusMessage("Error!")

            self.input_data = input_data
            self.oe_f2      = self.input_data.get_optical_element().inner_wise_optical_element.f2/self.workspace_units_to_m

            if self.is_automatic_run: self.compute()

    def build_gui(self):
        runaction = OWAction("Find Best Focus Position", self)
        runaction.triggered.connect(self.do_best_focus_calculation)
        self.addAction(runaction)

        runaction = OWAction("Interrupt Best Focus Calculation", self)
        runaction.triggered.connect(self.stop_best_focus_calculation)
        self.addAction(runaction)

        self.view_type = 1
        self.button_box.setVisible(False)

        main_box = oasysgui.widgetBox(self.controlArea, "Detector Parameters", orientation="vertical", width=self.CONTROL_AREA_WIDTH-5)


        oasysgui.lineEdit(main_box, self, "detector_size", "Detector Size [" + u"\u03BC" + "m]", labelWidth=260, valueType=float, orientation="horizontal")

        gui.separator(main_box)

        gui.comboBox(main_box, self, "calculation_type", label="Numeric Integration",
                     items=["Automatic Number of Points", "User Defined Number of Points"], labelWidth=160,
                     callback=self.set_CalculationType, sendSelectedValue=False, orientation="horizontal")

        self.detector_box = oasysgui.widgetBox(main_box, "", orientation="vertical", width=self.CONTROL_AREA_WIDTH-25, height=30)

        le_calculated_number_of_points = oasysgui.lineEdit(self.detector_box, self, "calculated_number_of_points", "Calculated Number of Points", labelWidth=260, valueType=float, orientation="horizontal")
        le_calculated_number_of_points.setReadOnly(True)
        font = QFont(le_calculated_number_of_points.font())
        font.setBold(True)
        le_calculated_number_of_points.setFont(font)
        palette = QPalette(le_calculated_number_of_points.palette())
        palette.setColor(QPalette.Text, QColor('dark blue'))
        palette.setColor(QPalette.Base, QColor(243, 240, 160))
        le_calculated_number_of_points.setPalette(palette)

        self.number_box = oasysgui.widgetBox(main_box, "", orientation="vertical", width=self.CONTROL_AREA_WIDTH-25, height=30)

        oasysgui.lineEdit(self.number_box, self, "number_of_points", "Number of Points", labelWidth=260, valueType=int, orientation="horizontal")

        self.set_CalculationType()

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

        gui.button(main_box, self, "Compute", callback=self.compute, height=35)

        best_focus_box = oasysgui.widgetBox(self.controlArea, "Best Focus Calculation", orientation="vertical", width=self.CONTROL_AREA_WIDTH-5)

        self.le_defocus_start = oasysgui.lineEdit(best_focus_box, self, "defocus_start", "Defocus sweep start", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_defocus_stop  = oasysgui.lineEdit(best_focus_box, self, "defocus_stop", "Defocus sweep stop", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_defocus_step  = oasysgui.lineEdit(best_focus_box, self, "defocus_step", "Defocus sweep step", labelWidth=260, valueType=float, orientation="horizontal")

        gui.separator(best_focus_box, height=5)

        gui.checkBox(best_focus_box, self, "show_animation", "Show animation during calculation")

        gui.separator(best_focus_box, height=5)


        button_box = oasysgui.widgetBox(best_focus_box, "", orientation="horizontal", width=self.CONTROL_AREA_WIDTH-25)

        gui.button(button_box, self, "Find Best Focus Position", callback=self.do_best_focus_calculation, height=35)
        stop_button = gui.button(button_box, self, "Interrupt", callback=self.stop_best_focus_calculation, height=35)
        font = QFont(stop_button.font())
        font.setBold(True)
        stop_button.setFont(font)
        palette = QPalette(stop_button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('red'))
        stop_button.setPalette(palette) # assign new palette

        self.save_button = gui.button(best_focus_box, self, "Save Best Focus Calculation Complete Results", callback=self.save_best_focus_results, height=35)
        self.save_button.setEnabled(False)

        parallel_box = oasysgui.widgetBox(self.controlArea, "Parallel Computing", orientation="vertical", width=self.CONTROL_AREA_WIDTH-5)

        gui.comboBox(parallel_box, self, "use_multipool", label="Use Parallel Processing",
                     items=["No", "Yes"], labelWidth=260,
                     callback=self.set_Multipool, sendSelectedValue=False, orientation="horizontal")

        self.use_multipool_box = oasysgui.widgetBox(parallel_box, "", addSpace=True, orientation="vertical", height=30, width=self.CONTROL_AREA_WIDTH-25)
        self.use_multipool_box_empty = oasysgui.widgetBox(parallel_box, "", addSpace=True, orientation="vertical", height=30, width=self.CONTROL_AREA_WIDTH-25)

        oasysgui.lineEdit(self.use_multipool_box, self, "n_pools", "Nr. Parallel Processes", labelWidth=260, valueType=int, orientation="horizontal")

        self.set_Multipool()

        self.best_focus_slider = None

    def set_CalculationType(self):
        self.detector_box.setVisible(self.calculation_type==0)
        self.number_box.setVisible(self.calculation_type==1)

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
        self.detector_size = congruence.checkStrictlyPositiveNumber(self.detector_size, "Detector Size")

        if self.calculation_type == 1: #auto
            self.number_of_points = congruence.checkStrictlyPositiveNumber(self.number_of_points, "Number of Points")

        if self.oe_f2 + self.defocus_sweep <= 0: raise Exception("Defocus sweep reached the previous mirror")

        if self.use_multipool == 1:
            self.n_pools = congruence.checkStrictlyPositiveNumber(self.n_pools, "Nr. Parallel Processes")

            import multiprocessing
            number_of_cpus = multiprocessing.cpu_count()

            if number_of_cpus == 1:
                raise Exception("Parallel processing not available with 1 CPU")
            elif self.n_pools >= number_of_cpus:
                raise Exception("Max number of parallel processes allowed on this computer: " + str(number_of_cpus-1))

    def do_wise_calculation(self):
        if self.input_data is None:
            raise Exception("No Input Data!")

        detector_size = self.detector_size*1e-6

        if self.calculation_type == WiseNumericalIntegrationParameters.AUTOMATIC:
            number_of_points = -1
        else:
            number_of_points = self.number_of_points

        previous_numerical_integration_parameters = self.input_data.get_numerical_integration_parameters()
        numerical_integration_parameters = WiseNumericalIntegrationParameters(self.calculation_type, detector_size, number_of_points)

        propagation_type = WisePropagationParameters.MIRROR_AND_DETECTOR

        #
        # No need to recalculated wavefront on previous mirror surface
        # if numerical integration parameters are identical
        #
        if self.calculation_type == previous_numerical_integration_parameters.calculation_type:
            if self.calculation_type == WiseNumericalIntegrationParameters.AUTOMATIC:
                if detector_size == previous_numerical_integration_parameters.detector_size:
                    propagation_type = WisePropagationParameters.DETECTOR_ONLY
                    numerical_integration_parameters.calculated_number_of_points = previous_numerical_integration_parameters.calculated_number_of_points
            else:
                if self.number_of_points == previous_numerical_integration_parameters.number_of_points:
                    propagation_type = WisePropagationParameters.DETECTOR_ONLY
                    numerical_integration_parameters.calculated_number_of_points = previous_numerical_integration_parameters.calculated_number_of_points

        propagation_parameter = WisePropagationParameters(propagation_type=propagation_type,
                                                          source=self.input_data.get_source().inner_wise_source,
                                                          optical_element=self.input_data.get_optical_element().inner_wise_optical_element,
                                                          wavefront=self.input_data.get_wavefront(),
                                                          numerical_integration_parameters=numerical_integration_parameters,
                                                          defocus_sweep=self.defocus_sweep * self.workspace_units_to_m)

        propagation_output = WisePropagatorsChain.Instance().do_propagation(propagation_parameter,
                                                                            WisePropagationAlgorithms.HuygensIntegral)

        if self.calculation_type == 0:
            self.calculated_number_of_points = propagation_output.number_of_points
        else:
            self.calculated_number_of_points = 0

        positions_s = propagation_output.det_s
        electric_fields = propagation_output.electric_fields

        data_to_plot = numpy.zeros((5, len(positions_s)))
        data_to_plot[0, :] = positions_s * 1e6
        data_to_plot[1, :] = Amp(electric_fields)**2

        return data_to_plot

    def getTabTitles(self):
        return ["Intensity on O.E. Focus", "Intensity on Best Focus", "Hew"]

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

    def stop_best_focus_calculation(self):
        self.run_calculation = False

    def do_best_focus_calculation(self):
        try:
            if self.input_data is None:
                raise Exception("No Input Data!")

            sys.stdout = EmittingStream(textWritten=self.writeStdOut)

            self.check_fields()
            if self.defocus_start >= self.defocus_stop: raise Exception("Defocus sweep start must be < Defocus sweep stop")
            self.defocus_step = congruence.checkStrictlyPositiveNumber(self. defocus_step, "Defocus sweep step")
            if self.defocus_step >= self.defocus_stop - self.defocus_start: raise Exception("Defocus step is too big")

            if self.best_focus_slider is None:
                self.best_focus_slider = QSlider(self.tab[1])
                self.best_focus_slider.setGeometry(QRect(0, 0, 320, 50))
                self.best_focus_slider.setMinimumHeight(30)
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

            detector_size = self.detector_size*1e-6

            if self.calculation_type == 0:
                number_of_points = -1
            else:
                number_of_points = self.number_of_points

            previous_numerical_integration_parameters = self.input_data.get_numerical_integration_parameters()
            numerical_integration_parameters = WiseNumericalIntegrationParameters(self.calculation_type, detector_size, int(number_of_points))

            propagation_type = WisePropagationParameters.MIRROR_AND_DETECTOR

            #
            # No need to recalculated wavefront on previous mirror surface
            # if numerical integration parameters are identical
            #
            if self.calculation_type == previous_numerical_integration_parameters.calculation_type:
                if self.calculation_type == WiseNumericalIntegrationParameters.AUTOMATIC:
                    if detector_size == previous_numerical_integration_parameters.detector_size:
                        propagation_type = WisePropagationParameters.DETECTOR_ONLY
                        numerical_integration_parameters.calculated_number_of_points = previous_numerical_integration_parameters.calculated_number_of_points
                else:
                    if self.number_of_points == previous_numerical_integration_parameters.number_of_points:
                        propagation_type = WisePropagationParameters.DETECTOR_ONLY
                        numerical_integration_parameters.calculated_number_of_points = previous_numerical_integration_parameters.calculated_number_of_points

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

            hew_min = numpy.inf
            index_min_list = []

            self.best_focus_index = -1
            self.electric_fields_list = []
            self.positions_list = []
            self.hews_list = []

            propagation_parameter = WisePropagationParameters(propagation_type=propagation_type,
                                                              source=source,
                                                              optical_element=elliptic_mirror,
                                                              wavefront=self.input_data.get_wavefront(),
                                                              numerical_integration_parameters=numerical_integration_parameters,
                                                              n_pools=n_pools)


            self.setStatusMessage("Calculating Best Focus Position")

            self.run_calculation = True

            for i, defocus in enumerate(self.defocus_list):
                if not self.run_calculation:
                    if not self.best_focus_slider is None: self.best_focus_slider.valueChanged.connect(self.plot_detail)
                    return

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
                                    title="Defocus Sweep: " + str(defocus/self.workspace_units_to_m) + " (" + str(i+1) + "/" + str(n_defocus) +
                                          "), HEW: " + str(round(propagation_output.HEW*1e6, 4)) + " [$\mu$m]",
                                    xtitle="Z [$\mu$m]",
                                    ytitle="Intensity",
                                    log_x=False,
                                    log_y=False)

                    self.tabs.setCurrentIndex(1)
                else:
                    self.progressBarSet(value=i*progress_bar_increment)

                hew = round(propagation_output.HEW*1e6, 11) # problems with double precision numbers: inconsistent comparisons

                if hew < hew_min:
                    hew_min = hew
                    index_min_list = [i]
                elif hew == hew_min:
                    index_min_list.append(i)

            index_min = index_min_list[int(len(index_min_list)/2)] # choosing the central value, when hew reach a pletau

            self.best_focus_index = index_min
            best_focus_electric_fields = self.electric_fields_list[index_min]
            best_focus_positions       = self.positions_list[index_min]

            QMessageBox.information(self,
                                    "Best Focus Calculation",
                                    "Best Focus Found!\n\nPosition: " + str(self.oe_f2 + (self.defocus_list[index_min]/self.workspace_units_to_m)) +
                                    "\nHEW: " + str(round(self.hews_list[index_min]*1e6, 4)) + " [" + u"\u03BC" + "m]",
                                    QMessageBox.Ok
                                    )

            self.plot_histo(best_focus_positions * 1e6,
                            Amp(best_focus_electric_fields) ** 2,
                            100,
                            tabs_canvas_index=1,
                            plot_canvas_index=1,
                            title="(BEST FOCUS) Defocus Sweep: " + str(self.defocus_list[index_min]/self.workspace_units_to_m) +
                                  " ("+ str(index_min+1) + "/" + str(n_defocus) + "), Position: " +
                                  str(self.oe_f2 + (self.defocus_list[index_min]/self.workspace_units_to_m)) +
                                  ", HEW: " + str(round(self.hews_list[index_min]*1e6, 4)) + " [$\mu$m]",
                            xtitle="Z [$\mu$m]",
                            ytitle="Intensity",
                            log_x=False,
                            log_y=False)

            self.plot_histo(self.defocus_list,
                            numpy.multiply(self.hews_list, 1e6),
                            100,
                            tabs_canvas_index=2,
                            plot_canvas_index=2,
                            title="HEW vs Defocus Sweep",
                            xtitle="",
                            ytitle="",
                            log_x=False,
                            log_y=False)

            self.plot_canvas[2].setDefaultPlotLines(True)
            self.plot_canvas[2].setDefaultPlotPoints(True)
            self.plot_canvas[2].setGraphXLabel("Defocus [" + self.workspace_units_label + "]")
            self.plot_canvas[2].setGraphYLabel("HEW [$\mu$m]")

            self.best_focus_slider.setValue(index_min)

            self.tabs.setCurrentIndex(1)
            self.setStatusMessage("")

            self.save_button.setEnabled(True)

        except Exception as exception:
            QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

            self.setStatusMessage("Error!")

            #raise exception

        if not self.best_focus_slider is None: self.best_focus_slider.valueChanged.connect(self.plot_detail)
        self.progressBarFinished()


    def plot_detail(self, value):
        try:
            index = value
            n_defocus = len(self.positions_list)

            electric_fields = self.electric_fields_list[index]
            positions       = self.positions_list[index]

            if index == self.best_focus_index:
                title = "(BEST FOCUS) Defocus Sweep: " + str(self.defocus_list[index]/self.workspace_units_to_m) + \
                        " ("+ str(index+1) + "/" + str(n_defocus) + "), Position: " + \
                        str(self.oe_f2 + (self.defocus_list[index]/self.workspace_units_to_m)) + \
                        ", HEW: " + str(round(self.hews_list[index]*1e6, 4)) + " [$\mu$m]"
            else:
                title = "Defocus Sweep: " + str(self.defocus_list[index]/self.workspace_units_to_m) + \
                        " (" + str(index+1) + "/" + str(n_defocus) + "), HEW: " + str(round(self.hews_list[index]*1e6, 4)) + " [$\mu$m]"

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

                            file.write("# Defocus Sweep: " + str(self.defocus_list[index]) + " [m]\n")
                            file.write("# HEW          : " + str(self.hews_list[index]) + " [m]\n")
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
