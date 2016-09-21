import sys
import numpy
from PyQt4.QtGui import QApplication, QMessageBox
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from orangecontrib.wise.util.wise_objects import WiseOpticalElement, Wavefront, WiseOutput, WisePreInputData
from orangecontrib.wise.widgets.gui.ow_wise_widget import WiseWidget
from orangecontrib.wise.util.wise_propagator import WisePropagatorsChain, WisePropagationAlgorithms, WisePropagationParameters

from wiselib import Optics
from  wiselib.Rayman5 import Amp, Cyc

SOURCE = 0
OE = 1

class OWEllipticalMirror(WiseWidget):
    name = "EllipticalMirror"
    id = "EllipticalMirror"
    description = "EllipticalMirror"
    icon = "icons/elliptical_mirror.png"
    priority = 2
    category = ""
    keywords = ["wise", "elliptical"]

    inputs = [("Input", WiseOutput, "set_input"), ("PreInput", WisePreInputData, "set_pre_input")]

    f1 = Setting(98000)
    f2 = Setting(1200)
    alpha = Setting(2)
    length = Setting(400)
    use_figure_error = Setting(0)
    figure_error_file = Setting("figure_error.dat")
    figure_error_step = Setting(0.002)
    figure_error_um_conversion = Setting(1.0)
    use_roughness = Setting(0)
    roughness_file = Setting("roughness.dat")
    roughness_x_scaling = Setting(1.0)
    roughness_y_scaling = Setting(1.0)
    roughness_fit_data = Setting(0)
    detector_size = Setting(50)

    input_data = None

    def set_input(self, input_data):
        self.setStatusMessage("")

        if not input_data is None:
            if input_data.has_optical_element():
                QMessageBox.critical(self, "Error", "Propagation from previous O.E. not yet supported", QMessageBox.Ok)

                self.setStatusMessage("Error!")

            self.input_data = input_data


    def set_pre_input(self, data):
        if data is not None:
            if data.figure_error_file != WisePreInputData.NONE:
                self.figure_error_file = data.figure_error_file
                self.figure_error_step = data.figure_error_step
                self.figure_error_um_conversion = data.figure_user_units_to_m
                self.use_figure_error = 1

                self.set_UseFigureError()

            if data.roughness_file != WisePreInputData.NONE:
                self.roughness_file=data.roughness_file
                self.roughness_x_scaling = data.roughness_x_scaling
                self.roughness_y_scaling = data.roughness_y_scaling
                self.use_roughness = 1

                self.set_UseRoughness()

    def build_gui(self):
        main_box = oasysgui.widgetBox(self.controlArea, "Elliptical Mirror Input Parameters", orientation="vertical", width=self.CONTROL_AREA_WIDTH-5)

        self.le_f1 = oasysgui.lineEdit(main_box, self, "f1", "F1", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_f2 = oasysgui.lineEdit(main_box, self, "f2", "F2", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(main_box, self, "alpha", "Incidence Angle [deg]", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_length = oasysgui.lineEdit(main_box, self, "length", "Length", labelWidth=260, valueType=float, orientation="horizontal")

        gui.separator(main_box, height=5)

        gui.comboBox(main_box, self, "use_figure_error", label="Error Profile",
                     items=["None", "User Defined"], labelWidth=260,
                     callback=self.set_UseFigureError, sendSelectedValue=False, orientation="horizontal")

        self.use_figure_error_box = oasysgui.widgetBox(main_box, "", addSpace=True, orientation="vertical", height=70)
        self.use_figure_error_box_empty = oasysgui.widgetBox(main_box, "", addSpace=True, orientation="vertical", height=70)


        file_box =  oasysgui.widgetBox(self.use_figure_error_box, "", addSpace=False, orientation="horizontal")
        self.le_figure_error_file = oasysgui.lineEdit(file_box, self, "figure_error_file", "File Name", labelWidth=100, valueType=str, orientation="horizontal")
        gui.button(file_box, self, "...", callback=self.selectFigureErrorFile)

        self.le_figure_error_step = oasysgui.lineEdit(self.use_figure_error_box, self, "figure_error_step", "Step", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.use_figure_error_box, self, "figure_error_um_conversion", "user file u.m. to [m] factor", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_UseFigureError()

        gui.comboBox(main_box, self, "use_roughness", label="roughness",
                     items=["None", "User Defined"], labelWidth=260,
                     callback=self.set_UseRoughness, sendSelectedValue=False, orientation="horizontal")

        self.use_roughness_box = oasysgui.widgetBox(main_box, "", addSpace=True, orientation="vertical", height=100)
        self.use_roughness_box_empty = oasysgui.widgetBox(main_box, "", addSpace=True, orientation="vertical", height=100)

        file_box = oasysgui.widgetBox(self.use_roughness_box, "", addSpace=False, orientation="horizontal")
        self.le_roughness_file = oasysgui.lineEdit(file_box, self, "roughness_file", "File Name", labelWidth=100, valueType=str, orientation="horizontal")
        gui.button(file_box, self, "...", callback=self.selectroughnessFile)

        oasysgui.lineEdit(self.use_roughness_box, self, "roughness_x_scaling", "x user file u.m. to [m]   factor", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.use_roughness_box, self, "roughness_y_scaling", "y user file u.m. to [m^3] factor", labelWidth=260, valueType=float, orientation="horizontal")

        gui.comboBox(self.use_roughness_box, self, "roughness_fit_data", label="Fit numeric data with power law",
                     items=["No", "Yes"], labelWidth=260, sendSelectedValue=False, orientation="horizontal")

        self.set_UseRoughness()

        detector_box = oasysgui.widgetBox(self.controlArea, "Detector Parameters", orientation="vertical", width=self.CONTROL_AREA_WIDTH-5)

        oasysgui.lineEdit(detector_box, self, "detector_size", "Detector Size [" + u"\u03BC" + "m]", labelWidth=260, valueType=float, orientation="horizontal")

    def selectFigureErrorFile(self):
        self.le_figure_error_file.setText(oasysgui.selectFileFromDialog(self, self.figure_error_file, "Select File", file_extension_filter="Data Files (*.dat *.txt)"))

    def selectroughnessFile(self):
        self.le_roughness_file.setText(oasysgui.selectFileFromDialog(self, self.roughness_file, "Select File", file_extension_filter="Data Files (*.dat *.txt)"))

    def set_UseFigureError(self):
        self.use_figure_error_box.setVisible(self.use_figure_error == 1)
        self.use_figure_error_box_empty.setVisible(self.use_figure_error == 0)

    def set_UseRoughness(self):
        self.use_roughness_box.setVisible(self.use_roughness == 1)
        self.use_roughness_box_empty.setVisible(self.use_roughness == 0)

    def after_change_workspace_units(self):
        label = self.le_f1.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_f2.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_length.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_figure_error_step.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")

    def check_fields(self):
        self.f1 = congruence.checkStrictlyPositiveNumber(self.f1, "F1")
        self.f2 = congruence.checkStrictlyPositiveNumber(self.f2, "F2")
        self.alpha = congruence.checkAngle(self.alpha, "Incidence Angle")
        self.length = congruence.checkStrictlyPositiveNumber(self.length, "Length")

        if self.use_figure_error == 1:
            congruence.checkFileName(self.figure_error_file)

        if self.use_roughness == 1:
            congruence.checkFileName(self.roughness_file)

    def do_wise_calculation(self):
        if self.input_data is None:
            raise Exception("No Input Data!")

        elliptic_mirror = Optics.Ellipse(f1 = self.f1 * self.workspace_units_to_m,
                                         f2 = self.f2 * self.workspace_units_to_m,
                                         Alpha = numpy.radians(self.alpha),
                                         L = self.length * self.workspace_units_to_m)

        if self.use_figure_error == 1:
            elliptic_mirror.FigureErrorAdd(numpy.loadtxt(self.figure_error_file) * self.figure_error_um_conversion,
                                           self.figure_error_step * self.workspace_units_to_m) # (m)



        if self.use_roughness == 1:
            elliptic_mirror.Roughness.NumericPsdLoadXY(self.roughness_file,
                                                       xScaling = self.roughness_x_scaling * self.workspace_units_to_m,
                                                       yScaling = self.roughness_y_scaling * self.workspace_units_to_m,
                                                       xIsSpatialFreq = False)
            elliptic_mirror.Roughness.Options.FIT_NUMERIC_DATA_WITH_POWER_LAW = (self.roughness_fit_data == 1)
            elliptic_mirror.Options.USE_ROUGHNESS = True
        else:
            elliptic_mirror.Options.USE_ROUGHNESS = False

        #------------------------------------------------------------

        wise_source = self.input_data.get_source()

        if wise_source.get_property("source_on_mirror_focus"):
            wise_source.inner_wise_source = Optics.GaussianSource_1d(wise_source.inner_wise_source.Lambda,
                                                                     wise_source.inner_wise_source.Waist0,
                                                                     ZOrigin = elliptic_mirror.XYF1[0],
                                                                     YOrigin = elliptic_mirror.XYF1[1],
                                                                     Theta = elliptic_mirror.p1_Angle)



        propagation_parameter = WisePropagationParameters(source=wise_source.inner_wise_source,
                                                          optical_element=elliptic_mirror,
                                                          detector_size=self.detector_size*1e-6)


        propagation_output = WisePropagatorsChain.Instance().do_propagation(propagation_parameter,
                                                                            WisePropagationAlgorithms.HuygensIntegral)


        mir_E = propagation_output.mir_E
        mir_s = propagation_output.mir_s
        det_s = propagation_output.det_s
        electric_fields = propagation_output.electric_fields

        wise_optical_element = WiseOpticalElement(inner_wise_optical_element=elliptic_mirror)
        wise_optical_element.set_property("detector_size", self.detector_size*1e-6)

        data_to_plot = numpy.zeros((5, len(mir_s)))
        data_to_plot[0, :] = mir_s / self.workspace_units_to_m
        data_to_plot[1, :] = Amp(mir_E)
        data_to_plot[2, :] = Cyc(mir_E)
        data_to_plot[3, :] = det_s * 1e6
        data_to_plot[4, :] = Amp(electric_fields)**2

        return wise_source, \
               wise_optical_element, \
               Wavefront(electric_fields=electric_fields,
                         positions=det_s), \
               data_to_plot

    def getTabTitles(self):
        return ["|E0|: mirror", "Optical cycles", "Intensity on F2"]

    def getTitles(self):
        return ["|E0|: mirror", "Optical cycles", "Intensity on F2"]

    def getXTitles(self):
        return ["rho [" + self.workspace_units_label + "]", "Z [" + self.workspace_units_label + "]", "Z [$\mu$m]"]

    def getYTitles(self):
        return ["E0", "Optical Cycles", "Intensity"]

    def getVariablesToPlot(self):
        return [(0, 1), (0, 2), (3, 4)]

    def getLogPlot(self):
        return [(False, False), (False, False), (False, False)]

    def extract_plot_data_from_calculation_output(self, calculation_output):
        return calculation_output[3]

    def extract_wise_output_from_calculation_output(self, calculation_output):
        return WiseOutput(source=calculation_output[0],
                          optical_element=calculation_output[1],
                          wavefront=calculation_output[2])
