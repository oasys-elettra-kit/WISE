import sys
import numpy
from scipy.stats import norm
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

    z_origin = Setting(0.0)
    x_origin = Setting(0.0)
    theta = Setting(0.0)

    wofry_wavefront = None

    def build_gui(self):

        main_box = oasysgui.widgetBox(self.controlArea, "Wofry Wavefront Parameters", orientation="vertical", width=self.CONTROL_AREA_WIDTH-5, height=200)

        oasysgui.lineEdit(main_box, self, "source_lambda", "Wavelength [nm]", labelWidth=260, valueType=float, orientation="horizontal")

        gui.separator(main_box, height=5)

        self.source_position_box_1 = oasysgui.widgetBox(main_box, "", addSpace=True, orientation="vertical", height=70)

        self.le_z_origin = oasysgui.lineEdit(self.source_position_box_1, self, "z_origin", "Z Origin", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_x_origin = oasysgui.lineEdit(self.source_position_box_1, self, "x_origin", "X Origin", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.source_position_box_1, self, "theta", "Theta [deg]", labelWidth=260, valueType=float, orientation="horizontal")

    def after_change_workspace_units(self):
        label = self.le_z_origin.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_x_origin.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")


    def check_fields(self):
        self.source_lambda = congruence.checkStrictlyPositiveNumber(self.source_lambda, "Wavelength")
        self.theta = congruence.checkAngle(self.theta, "Theta")

    def do_wise_calculation(self):
        #self.z_origin = 0.0
        #self.x_origin = 0.0
        #self.theta    = 0.0

        wise_inner_source = WofryWavefrontSource_1d(wofry_wavefront=self.wofry_wavefront,
                                                    ZOrigin = self.z_origin * self.workspace_units_to_m,
                                                    YOrigin =  self.x_origin * self.workspace_units_to_m,
                                                    Theta = numpy.radians(self.theta))

        data_to_plot = numpy.zeros((2, 100))

        data_to_plot[0, :] = self.wofry_wavefront._electric_field_array.get_abscissas()
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
        wise_source.set_property("source_on_mirror_focus", False)

        return WiseOutput(source=wise_source)


    def set_input(self, input_data):
        self.setStatusMessage("")

        if not input_data is None:
            self.wofry_wavefront = input_data
            self.source_lambda = round(self.wofry_wavefront._wavelength*1e9, 4)

            if self.is_automatic_run: self.compute()

from wiselib import Rayman

class WofryWavefrontSource_1d(object):
    #================================================
    #     __init__
    #================================================
    def __init__(self, wofry_wavefront=GenericWavefront1D(), ZOrigin = 0, YOrigin = 0, Theta = 0):
        self.wofry_wavefront=wofry_wavefront
        self.Lambda = self.wofry_wavefront._wavelength

        self.Name = 'Wofry Wavefront @ %0.2fnm' % (self.Lambda *1e9)

        self.ZOrigin = ZOrigin
        self.YOrigin = YOrigin
        self.RhoZOrigin = numpy.array([YOrigin, ZOrigin])
        self.ThetaPropagation = Theta

    #================================================
    #     EvalField
    #================================================
    def EvalField_XYLab(self, x = numpy.array(None), y = numpy.array(None)):

        wav_E = self.wofry_wavefront._electric_field_array.get_values()
        wav_x = numpy.zeros(len(wav_E)) + self.YOrigin
        wav_y = self.wofry_wavefront._electric_field_array.get_abscissas() + self.ZOrigin

        electric_fields = Rayman.HuygensIntegral_1d_MultiPool(self.Lambda,
                                                              wav_E,
                                                              wav_x,
                                                              wav_y,
                                                              x,
                                                              y)

        return electric_fields
