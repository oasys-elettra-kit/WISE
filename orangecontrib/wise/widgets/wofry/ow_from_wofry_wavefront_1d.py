import numpy
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from orangecontrib.wise.util.wise_objects import WiseSource, WiseOutput
from orangecontrib.wise.widgets.gui.ow_wise_widget import WiseWidget

from wofry.propagator.wavefront1D.generic_wavefront import GenericWavefront1D

class OWFromWofryWavefront1d(WiseWidget):
    name = "From Wofry Wavefront 1D"
    id = "FromWofryWavefront1d"
    description = "From Wofry Wavefront 1D"
    icon = "icons/from_wofry_wavefront_1d.png"
    priority = 1
    category = ""
    keywords = ["wise", "gaussian"]

    inputs = [("GenericWavefront1D", GenericWavefront1D, "set_input")]

    source_lambda = Setting(10)
    source_position = Setting(0)

    z_origin = Setting(0.0)
    x_origin = Setting(0.0)
    theta = Setting(0.0)

    longitudinal_correction = Setting(0.0)
    transverse_correction = Setting(0.0)
    delta_theta = Setting(0.0)

    reset_phase = Setting(1)
    normalization_factor = Setting(1000)

    wofry_wavefront = None

    def build_gui(self):

        main_box = oasysgui.widgetBox(self.controlArea, "Wofry Wavefront Parameters", orientation="vertical", width=self.CONTROL_AREA_WIDTH-5, height=300)

        oasysgui.lineEdit(main_box, self, "source_lambda", "Wavelength [nm]", labelWidth=260, valueType=float, orientation="horizontal")

        gui.separator(main_box, height=5)

        gui.comboBox(main_box, self, "source_position", label="Source Position",
                                            items=["User Defined", "Put Source at Mirror Focus"], labelWidth=260,
                                            callback=self.set_SourcePosition, sendSelectedValue=False, orientation="horizontal")

        self.source_position_box_1 = oasysgui.widgetBox(main_box, "", addSpace=False, orientation="vertical", height=70)
        self.source_position_box_2 = oasysgui.widgetBox(main_box, "", addSpace=False, orientation="vertical", height=70)

        self.le_z_origin = oasysgui.lineEdit(self.source_position_box_1, self, "z_origin", "Z Origin", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_x_origin = oasysgui.lineEdit(self.source_position_box_1, self, "x_origin", "X Origin", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.source_position_box_1, self, "theta", "Theta [deg]", labelWidth=260, valueType=float, orientation="horizontal")

        self.le_longitudinal_correction = oasysgui.lineEdit(self.source_position_box_2, self, "longitudinal_correction", "Longitudinal correction", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_transverse_correction = oasysgui.lineEdit(self.source_position_box_2, self, "transverse_correction", "Transverse correction", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.source_position_box_2, self, "delta_theta", "\u0394" + "Theta [deg]", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_SourcePosition()

        gui.separator(main_box, height=5)

        gui.comboBox(main_box, self, "reset_phase", label="Reset Phase",
                                            items=["No", "Yes"], labelWidth=300, sendSelectedValue=False, orientation="horizontal")

        oasysgui.lineEdit(main_box, self, "normalization_factor", "Normalization Factor", labelWidth=260, valueType=float, orientation="horizontal")

    def set_SourcePosition(self):
        self.source_position_box_1.setVisible(self.source_position == 0)
        self.source_position_box_2.setVisible(self.source_position == 1)

    def after_change_workspace_units(self):
        label = self.le_z_origin.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_x_origin.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_longitudinal_correction.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_transverse_correction.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")


    def check_fields(self):
        self.source_lambda = congruence.checkStrictlyPositiveNumber(self.source_lambda, "Wavelength")

        if self.source_position == 0:
            self.longitudinal_correction = congruence.checkNumber(self.longitudinal_correction, "Longitudinal Correction")
            self.transverse_correction = congruence.checkNumber(self.transverse_correction, "Transverse Correction")
            self.delta_theta = congruence.checkAngle(self.delta_theta, "\u0394" + "Theta")
        else:
            self.theta = congruence.checkAngle(self.theta, "Theta")

    def do_wise_calculation(self):
        if self.source_position == 1:
            self.z_origin = 0.0
            self.x_origin = 0.0
            self.theta    = 0.0

        rinorm = numpy.sqrt(self.normalization_factor/numpy.max(self.wofry_wavefront.get_intensity()))

        if self.reset_phase:
            electric_fields = self.wofry_wavefront.get_amplitude()*rinorm + 0j
        else:
            electric_fields = self.wofry_wavefront.get_amplitude()*rinorm + self.wofry_wavefront.get_phase()

        self.wofry_wavefront.set_complex_amplitude(electric_fields)

        wise_inner_source = WofryWavefrontSource_1d(wofry_wavefront=self.wofry_wavefront,
                                                    ZOrigin = self.z_origin * self.workspace_units_to_m,
                                                    YOrigin =  self.x_origin * self.workspace_units_to_m,
                                                    Theta = numpy.radians(self.theta),
                                                    units_converter=self.workspace_units_to_m)

        data_to_plot = numpy.zeros((2, self.wofry_wavefront.size()))

        data_to_plot[0, :] = self.wofry_wavefront._electric_field_array.get_abscissas()/self.workspace_units_to_m
        data_to_plot[1, :] = numpy.abs(self.wofry_wavefront._electric_field_array.get_values())**2

        return wise_inner_source, data_to_plot

    def getTitles(self):
        return ["Wavefront Intensity"]

    def getXTitles(self):
        return ["Z [" + self.workspace_units_label + "]"]

    def getYTitles(self):
        return ["Intensity [arbitrary units]"]

    def extract_plot_data_from_calculation_output(self, calculation_output):
        return calculation_output[1]

    def extract_wise_output_from_calculation_output(self, calculation_output):
        wise_source = WiseSource(inner_wise_source=calculation_output[0])
        wise_source.set_property("source_on_mirror_focus", self.source_position == 1)

        if self.source_position == 1:
            wise_source.set_property("longitudinal_correction", self.longitudinal_correction)
            wise_source.set_property("transverse_correction", self.transverse_correction)
            wise_source.set_property("delta_theta", self.delta_theta)

        return WiseOutput(source=wise_source)

    def set_input(self, input_data):
        self.setStatusMessage("")

        if not input_data is None:
            self.wofry_wavefront = input_data.duplicate()
            self.source_lambda = round(self.wofry_wavefront._wavelength*1e9, 4)

            if self.is_automatic_run: self.compute()

from wiselib import Rayman

class WofryWavefrontSource_1d(object):
    #================================================
    #     __init__
    #================================================
    def __init__(self, wofry_wavefront=GenericWavefront1D(), ZOrigin = 0, YOrigin = 0, Theta = 0, units_converter=1e-2):
        self.wofry_wavefront=wofry_wavefront
        self.Lambda = self.wofry_wavefront._wavelength
        self.Name = 'Wofry Wavefront @ %0.2fnm' % (self.Lambda *1e9)

        self.ZOrigin = ZOrigin
        self.YOrigin = YOrigin
        self.ThetaPropagation = Theta

        parameters, covariance_matrix_pv = WofryWavefrontSource_1d.gaussian_fit(self.wofry_wavefront.get_intensity(), self.wofry_wavefront.get_abscissas())

        self.Waist0 = parameters[3]

        self.units_converter = units_converter

    #================================================
    #     EvalField
    #================================================
    def EvalField_XYLab(self, x = numpy.array(None), y = numpy.array(None)):
        wav_E = self.wofry_wavefront._electric_field_array.get_values()
        wav_x = numpy.zeros(len(wav_E)) + self.ZOrigin
        wav_y = self.wofry_wavefront._electric_field_array.get_abscissas()*self.units_converter + self.YOrigin

        electric_fields = Rayman.HuygensIntegral_1d_MultiPool(self.Lambda,
                                                              wav_E,
                                                              wav_x,
                                                              wav_y,
                                                              x,
                                                              y)
        return electric_fields



    def EvalField_XYSelf(self, x = numpy.array(None), y = numpy.array(None)):
        wav_E = self.wofry_wavefront._electric_field_array.get_values()
        wav_x = numpy.zeros(len(wav_E)) + self.ZOrigin
        wav_y = self.wofry_wavefront._electric_field_array.get_abscissas()*self.units_converter + self.YOrigin

        electric_fields = Rayman.HuygensIntegral_1d_MultiPool(self.Lambda,
                                                              wav_E,
                                                              wav_x,
                                                              wav_y,
                                                              x,
                                                              y)

        return electric_fields


    @classmethod
    def gaussian_fit(cls, data_x, data_y):
        from scipy import optimize, asarray

        x = asarray(data_x)
        y = asarray(data_y)
        y_norm = y/sum(y)

        mean = sum(x*y_norm)
        sigma = numpy.sqrt(sum(y_norm*(x-mean)**2)/len(x))
        amplitude = max(y)

        parameters, covariance_matrix = optimize.curve_fit(WofryWavefrontSource_1d.gaussian_function, x, y, p0 = [amplitude, mean, sigma])
        parameters.resize(4)
        parameters[3] = 2.355*parameters[2]# FWHM

        return parameters, covariance_matrix

    @classmethod
    def gaussian_function(cls, x, A, x0, sigma):
        return A*numpy.exp(-(x-x0)**2/(2*sigma**2))
