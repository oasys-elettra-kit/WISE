import sys
import numpy
from PyMca5.PyMcaGui.plotting.PlotWindow import PlotWindow
from PyQt4.QtCore import QRect
from PyQt4.QtGui import QTextEdit, QTextCursor, QApplication, QFont, QPalette, QColor, \
    QMessageBox

from srxraylib.metrology import profiles_simulation
from oasys.widgets.widget import OWWidget
from orangewidget import gui, widget
from orangewidget.settings import Setting

from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.widgets.gui import ConfirmDialog


from orangecontrib.wise.util.wise_objects import WisePreInputData
from orangecontrib.wise.util.wise_util import EmittingStream, WisePlot

class OWheight_profile_simulator(OWWidget):
    name = "Height Profile Simulator"
    id = "height_profile_simulator"
    description = "Calculation of mirror surface height profile"
    icon = "icons/simulator.png"
    author = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi@elettra.eu"
    priority = 1
    category = ""
    keywords = ["height_profile_simulator"]

    outputs = [{"name": "PreInput",
                "type": WisePreInputData,
                "doc": "PreInput",
                "id": "PreInput"}]

    want_main_area = 1
    want_control_area = 1

    MAX_WIDTH = 1320
    MAX_HEIGHT = 700

    IMAGE_WIDTH = 860
    IMAGE_HEIGHT = 645

    CONTROL_AREA_WIDTH = 405
    TABS_AREA_HEIGHT = 618

    xx = None
    yy = None

    kind_of_profile_y = Setting(0)
    step_y = Setting(1.0)
    dimension_y = Setting(200.1)
    power_law_exponent_beta_y = Setting(1.5)
    correlation_length_y = Setting(30.0)
    rms_y = Setting(1)
    montecarlo_seed_y = Setting(8788)
    error_type_y = Setting(profiles_simulation.FIGURE_ERROR)

    heigth_profile_file_name = Setting('figure_error.dat')

    def __init__(self):
        super().__init__()

        self.runaction = widget.OWAction("Calculate Height Profile", self)
        self.runaction.triggered.connect(self.calculate_heigth_profile)
        self.addAction(self.runaction)

        self.runaction = widget.OWAction("Generate Height Profile File", self)
        self.runaction.triggered.connect(self.generate_heigth_profile_file)
        self.addAction(self.runaction)

        geom = QApplication.desktop().availableGeometry()
        self.setGeometry(QRect(round(geom.width() * 0.05),
                               round(geom.height() * 0.05),
                               round(min(geom.width() * 0.98, self.MAX_WIDTH)),
                               round(min(geom.height() * 0.95, self.MAX_HEIGHT))))

        self.setMaximumHeight(self.geometry().height())
        self.setMaximumWidth(self.geometry().width())

        gui.separator(self.controlArea)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Calculate Height\nProfile", callback=self.calculate_heigth_profile)
        button.setFixedHeight(45)

        button = gui.button(button_box, self, "Generate Height\nProfile File", callback=self.generate_heigth_profile_file)
        font = QFont(button.font())
        font.setBold(True)
        button.setFont(font)
        palette = QPalette(button.palette())  # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Blue'))
        button.setPalette(palette)  # assign new palette
        button.setFixedHeight(45)
        button.setFixedWidth(150)

        button = gui.button(button_box, self, "Reset Fields", callback=self.call_reset_settings)
        font = QFont(button.font())
        font.setItalic(True)
        button.setFont(font)
        palette = QPalette(button.palette())  # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Red'))
        button.setPalette(palette)  # assign new palette
        button.setFixedHeight(45)

        gui.separator(self.controlArea)

        tabs_setting = gui.tabWidget(self.controlArea)
        tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT)
        tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        tab_input = oasysgui.createTabPage(tabs_setting, "Input Parameters")
        tab_out = oasysgui.createTabPage(tabs_setting, "Output")


        #/ ---------------------------------------

        input_box_l = oasysgui.widgetBox(tab_input, "Calculation Parameters", addSpace=True, orientation="vertical")

        gui.comboBox(input_box_l, self, "kind_of_profile_y", label="Kind of Profile", labelWidth=260,
                     items=["Fractal", "Gaussian"],
                     callback=self.set_KindOfProfileY, sendSelectedValue=False, orientation="horizontal")

        gui.separator(input_box_l)

        self.kind_of_profile_y_box_1 = oasysgui.widgetBox(input_box_l, "", addSpace=True, orientation="vertical", height=230)

        self.le_dimension_y = oasysgui.lineEdit(self.kind_of_profile_y_box_1, self, "dimension_y", "Dimensions",
                           labelWidth=260, valueType=float, orientation="horizontal")
        self.le_step_y = oasysgui.lineEdit(self.kind_of_profile_y_box_1, self, "step_y", "Step",
                           labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.kind_of_profile_y_box_1, self, "montecarlo_seed_y", "Monte Carlo initial seed", labelWidth=260,
                           valueType=int, orientation="horizontal")

        self.kind_of_profile_y_box_1_1 = oasysgui.widgetBox(self.kind_of_profile_y_box_1, "", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(self.kind_of_profile_y_box_1_1, self, "power_law_exponent_beta_y", "Beta Value",
                           labelWidth=260, valueType=float, orientation="horizontal")

        self.kind_of_profile_y_box_1_2 = oasysgui.widgetBox(self.kind_of_profile_y_box_1, "", addSpace=True, orientation="vertical")

        self.le_correlation_length_y = oasysgui.lineEdit(self.kind_of_profile_y_box_1_2, self, "correlation_length_y", "Correlation Length",
                           labelWidth=260, valueType=float, orientation="horizontal")

        gui.separator(self.kind_of_profile_y_box_1)

        gui.comboBox(self.kind_of_profile_y_box_1, self, "error_type_y", label="Normalization to", labelWidth=270,
                     items=["Figure Error (nm)", "Slope Error (" + "\u03BC" + "rad)"],
                     sendSelectedValue=False, orientation="horizontal")

        oasysgui.lineEdit(self.kind_of_profile_y_box_1, self, "rms_y", "Rms Value",
                          labelWidth=260, valueType=float, orientation="horizontal")


        self.set_KindOfProfileY()

        self.output_box = oasysgui.widgetBox(tab_input, "Outputs", addSpace=True, orientation="vertical")

        self.select_file_box = oasysgui.widgetBox(self.output_box, "", addSpace=True, orientation="horizontal")

        self.le_heigth_profile_file_name = oasysgui.lineEdit(self.select_file_box, self, "heigth_profile_file_name", "Output File Name",
                                                        labelWidth=120, valueType=str, orientation="horizontal")

        gui.button(self.select_file_box, self, "...", callback=self.selectFile)

        self.shadow_output = QTextEdit()
        self.shadow_output.setReadOnly(True)

        out_box = oasysgui.widgetBox(tab_out, "System Output", addSpace=True, orientation="horizontal", height=580)
        out_box.layout().addWidget(self.shadow_output)

        gui.rubber(self.controlArea)

        main_tabs = gui.tabWidget(self.mainArea)
        self.plot_tab = gui.createTabPage(main_tabs, "Results")
        self.plot_tab.setFixedHeight(self.IMAGE_HEIGHT)
        self.plot_tab.setFixedWidth(self.IMAGE_WIDTH)

        self.plot_canvas = None

        gui.rubber(self.mainArea)

    def after_change_workspace_units(self):
        label = self.le_dimension_y.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_step_y.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_correlation_length_y.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")

    def set_KindOfProfileY(self):
        self.kind_of_profile_y_box_1_1.setVisible(self.kind_of_profile_y==0)
        self.kind_of_profile_y_box_1_2.setVisible(self.kind_of_profile_y==1)

    def calculate_heigth_profile(self, not_interactive_mode=False):
        try:
            sys.stdout = EmittingStream(textWritten=self.writeStdOut)

            self.check_fields()

            if self.error_type_y == profiles_simulation.FIGURE_ERROR:
                rms_y = self.rms_y * 1e-7 # from nm to cm
            else:
                rms_y = self.rms_y * 1e-6 # from urad to rad


            xx, yy = profiles_simulation.simulate_profile_1D(step = self.step_y * self.workspace_units_to_cm,
                                                             mirror_length = self.dimension_y * (self.workspace_units_to_cm),
                                                             random_seed = self.montecarlo_seed_y,
                                                             error_type = self.error_type_y,
                                                             profile_type=1-self.kind_of_profile_y,
                                                             rms = rms_y,
                                                             correlation_length = self.correlation_length_y * (self.workspace_units_to_cm),
                                                             power_law_exponent_beta = self.power_law_exponent_beta_y)

            xx_to_plot = xx/self.workspace_units_to_cm # to user units
            yy_to_plot = yy * 1e7 # nm
            self.yy = yy/self.workspace_units_to_cm # to user units

            ny = yy.size

            slope = numpy.zeros(ny)
            for i in range(ny-1):
                step = xx[i+1] - xx[i]
                slope[i] = numpy.arctan((yy[i+1] - yy[i]) / step)
            slope[ny-1] = slope[ny-2]
            sloperms = slope.std()

            title = ' Slope error rms in Y direction: %f $\mu$rad' % (sloperms*1e6)

            if self.plot_canvas is None:
                self.plot_canvas = PlotWindow(roi=False, control=False, position=False, plugins=False)
                self.plot_canvas.setDefaultPlotLines(True)
                self.plot_canvas.setActiveCurveColor(color='darkblue')

                self.plot_tab.layout().addWidget(self.plot_canvas)

            WisePlot.plot_histo(self.plot_canvas, xx_to_plot, yy_to_plot, title, "X [" + self.workspace_units_label + "]", "Y [nm]")

            QMessageBox.information(self, "QMessageBox.information()",
                                    "Height Profile calculated: if the result is satisfactory,\nclick \'Generate Height Profile File\' to complete the operation ",
                                    QMessageBox.Ok)
        except Exception as exception:
            QMessageBox.critical(self, "Error",
                                 exception.args[0],
                                 QMessageBox.Ok)
            raise exception

    def generate_heigth_profile_file(self, not_interactive_mode=False):
        if not self.yy is None:
            try:
                congruence.checkDir(self.heigth_profile_file_name)

                sys.stdout = EmittingStream(textWritten=self.writeStdOut)

                numpy.savetxt(self.heigth_profile_file_name, self.yy)

                QMessageBox.information(self, "QMessageBox.information()",
                                            "Height Profile file " + self.heigth_profile_file_name + " written on disk",
                                            QMessageBox.Ok)


                self.send("PreInput", WisePreInputData(figure_error_file=self.heigth_profile_file_name,
                                                       figure_error_step=self.step_y*self.workspace_units_to_cm*1e-2,
                                                       figure_user_units_to_m=self.workspace_units_to_cm*1e-2))
            except Exception as exception:
                QMessageBox.critical(self, "Error",
                                     exception.args[0],
                                     QMessageBox.Ok)

    def call_reset_settings(self):
        if ConfirmDialog.confirmed(parent=self, message="Confirm Reset of the Fields?"):
            try:
                self.resetSettings()
            except:
                pass

    def check_fields(self):
        self.dimension_y = congruence.checkStrictlyPositiveNumber(self.dimension_y, "Dimension")
        self.step_y = congruence.checkStrictlyPositiveNumber(self.step_y, "Step")
        if self.kind_of_profile_y == 0: self.power_law_exponent_beta_y = congruence.checkPositiveNumber(self.power_law_exponent_beta_y, "Beta Value")
        if self.kind_of_profile_y == 1: self.correlation_length_y = congruence.checkStrictlyPositiveNumber(self.correlation_length_y, "Correlation Length")
        self.rms_y = congruence.checkPositiveNumber(self.rms_y, "Rms")
        self.montecarlo_seed_y = congruence.checkPositiveNumber(self.montecarlo_seed_y, "Monte Carlo initial seed")

        congruence.checkDir(self.heigth_profile_file_name)

    def writeStdOut(self, text):
        cursor = self.shadow_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.shadow_output.setTextCursor(cursor)
        self.shadow_output.ensureCursorVisible()

    def selectFile(self):
        self.le_heigth_profile_file_name.setText(oasysgui.selectFileFromDialog(self, self.heigth_profile_file_name, "Select Output File", file_extension_filter="Data Files (*.dat *.txt)"))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = OWheight_profile_simulator()
    w.show()
    app.exec()
    w.saveSettings()
