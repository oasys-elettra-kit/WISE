import sys
import numpy
from PyQt4.QtGui import QApplication
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from orangecontrib.wise.util.wise_objects import WiseOpticalElement, Wavefront, WiseOutput, WisePreInputData
from orangecontrib.wise.widgets.gui.ow_wise_widget import WiseWidget

from wiselib import Optics
import wiselib.Rayman5 as Rayman
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

    f1 = Setting(98)
    f2 = Setting(1.2)
    alpha = Setting(2)
    length = Setting(0.4)
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

    def set_input(self, input_data):
        self.input_data = input_data

        if self.input_data.has_optical_elements():
            self.previous_type = OE
        else:
           self.previous_type = SOURCE

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

        oasysgui.lineEdit(main_box, self, "f1", "F1 [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(main_box, self, "f2", "F2 [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(main_box, self, "alpha", "Incidence Angle [deg]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(main_box, self, "length", "Length [m]", labelWidth=260, valueType=float, orientation="horizontal")

        gui.separator(main_box, height=5)

        gui.comboBox(main_box, self, "use_figure_error", label="Error Profile",
                     items=["None", "User Defined"], labelWidth=260,
                     callback=self.set_UseFigureError, sendSelectedValue=False, orientation="horizontal")

        self.use_figure_error_box = oasysgui.widgetBox(main_box, "", addSpace=True, orientation="vertical", height=70)
        self.use_figure_error_box_empty = oasysgui.widgetBox(main_box, "", addSpace=True, orientation="vertical", height=70)


        file_box =  oasysgui.widgetBox(self.use_figure_error_box, "", addSpace=False, orientation="horizontal")
        self.le_figure_error_file = oasysgui.lineEdit(file_box, self, "figure_error_file", "File Name", labelWidth=100, valueType=str, orientation="horizontal")
        gui.button(file_box, self, "...", callback=self.selectFigureErrorFile)

        oasysgui.lineEdit(self.use_figure_error_box, self, "figure_error_step", "Step [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.use_figure_error_box, self, "figure_error_um_conversion", "user u.m. to [m] factor", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_UseFigureError()

        gui.comboBox(main_box, self, "use_roughness", label="roughness",
                     items=["None", "User Defined"], labelWidth=260,
                     callback=self.set_UseRoughness, sendSelectedValue=False, orientation="horizontal")

        self.use_roughness_box = oasysgui.widgetBox(main_box, "", addSpace=True, orientation="vertical", height=100)
        self.use_roughness_box_empty = oasysgui.widgetBox(main_box, "", addSpace=True, orientation="vertical", height=100)

        file_box = oasysgui.widgetBox(self.use_roughness_box, "", addSpace=False, orientation="horizontal")
        self.le_roughness_file = oasysgui.lineEdit(file_box, self, "roughness_file", "File Name", labelWidth=100, valueType=str, orientation="horizontal")
        gui.button(file_box, self, "...", callback=self.selectroughnessFile)

        oasysgui.lineEdit(self.use_roughness_box, self, "roughness_x_scaling", "x user u.m. to [m]   factor", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.use_roughness_box, self, "roughness_y_scaling", "y user u.m. to [m^3] factor", labelWidth=260, valueType=float, orientation="horizontal")

        gui.comboBox(self.use_roughness_box, self, "roughness_fit_data", label="Fit numeric data with power law",
                     items=["No", "Yes"], labelWidth=260, sendSelectedValue=False, orientation="horizontal")

        self.set_UseRoughness()

        detector_box = oasysgui.widgetBox(self.controlArea, "Detector Parameters", orientation="vertical", width=self.CONTROL_AREA_WIDTH-5)

        oasysgui.lineEdit(detector_box, self, "detector_size", "detector_size [" + u"\u03BC" + "m]", labelWidth=260, valueType=float, orientation="horizontal")

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
        if self.previous_type == OE:
            raise Exception("Propagation from previous O.E. not yet supported")
        elif self.previous_type == SOURCE:
            elliptic_mirror = Optics.Ellipse(f1 = self.f1,
                                             f2 = self.f2,
                                             Alpha = self.alpha*numpy.pi/180,
                                             L = self.length)

            if self.use_figure_error == 1:
                elliptic_mirror.FigureErrorAdd(numpy.loadtxt(self.figure_error_file) * self.figure_error_um_conversion,
                                               self.figure_error_step) # (m)



            if self.use_roughness == 1:
                elliptic_mirror.Roughness.NumericPsdLoadXY(self.roughness_file,
                                                           xScaling = self.roughness_x_scaling,
                                                           yScaling = self.roughness_y_scaling,
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


            # Auto Sampling (easy way)
            # Info da: Fascio(Lambda), piano kb e piano detector
            theta_0 = elliptic_mirror.pTan_Angle
            theta_1 = numpy.arctan(-1/elliptic_mirror.p2[0])
            det_size = self.detector_size*1e-6
            n_auto = Rayman.SamplingCalculator(wise_source.inner_wise_source.Lambda,
                                               elliptic_mirror.f2,
                                               elliptic_mirror.L,
                                               det_size,
                                               theta_0,
                                               theta_1)


            # Piano specchio (Sorgente=>Specchio)
            mir_x, mir_y = elliptic_mirror.GetXY_MeasuredMirror(n_auto, 0)
            mir_E = wise_source.inner_wise_source.EvalField_XYLab(mir_x, mir_y)
            mir_s = Rayman.xy_to_s(mir_x, mir_y)

            # wave front at F2
            det_x, det_y = elliptic_mirror.GetXY_TransversePlaneAtF2(det_size, n_auto, 0.0)
            det_s = Rayman.xy_to_s(det_x, det_y)

            electric_fields = Rayman.HuygensIntegral_1d_MultiPool(wise_source.inner_wise_source.Lambda,
                                                                  mir_E,
                                                                  mir_x,
                                                                  mir_y,
                                                                  det_x,
                                                                  det_y,
                                                                  0)

            wise_optical_element = WiseOpticalElement(inner_wise_optical_element=elliptic_mirror)
            wise_optical_element.set_property("detector_size", det_size)

            data_to_plot = numpy.zeros((5, n_auto))
            data_to_plot[0, :] = mir_s * 1e3
            data_to_plot[1, :] = Amp(mir_E)
            data_to_plot[2, :] = Cyc(mir_E)
            data_to_plot[3, :] = det_s * 1e6
            data_to_plot[4, :] = Amp(electric_fields)**2

            return wise_source, \
                   wise_optical_element, \
                   Wavefront(electric_fields=electric_fields,
                             positions=det_s), \
                   data_to_plot
        else:
            raise Exception("Previous element not recognized")

    def getTitles(self):
        return ["|E0|: mirror", "Optical cycles", "Intensity on F2"]

    def getXTitles(self):
        return ["rho [mm]", "Z [mm]", "Z [$\mu$m]"]

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
