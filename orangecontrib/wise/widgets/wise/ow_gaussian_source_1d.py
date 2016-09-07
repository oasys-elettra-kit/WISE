import sys
import numpy
from PyQt4.QtGui import QApplication
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from orangecontrib.wise.util.wise_objects import WiseSource, WiseOutput
from orangecontrib.wise.widgets.gui.ow_wise_widget import WiseWidget

from wiselib import Optics

class OWGaussianSource1d(WiseWidget):
    name = "GaussianSource1d"
    id = "GaussianSource1d"
    description = "GaussianSource1d"
    icon = "icons/gaussian_source_1d.png"
    priority = 1
    category = ""
    keywords = ["wise", "gaussian"]

    source_lambda = Setting(10e-9)
    source_sigma =  Setting(125e-6)
    source_position = Setting(0)

    z_origin = Setting(0.0)
    x_origin = Setting(0.0)
    theta = Setting(0.0)

    def build_gui(self):

        main_box = oasysgui.widgetBox(self.controlArea, "Gaussian Source 1D Input Parameters", orientation="vertical", width=self.CONTROL_AREA_WIDTH-5, height=200)

        oasysgui.lineEdit(main_box, self, "source_lambda", "Wavelength [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(main_box, self, "source_sigma", "Sigma [m]", labelWidth=260, valueType=float, orientation="horizontal")

        gui.separator(main_box, height=5)

        gui.comboBox(main_box, self, "source_position", label="Source Position",
                                            items=["User Defined", "Put Source of Mirror Focus"], labelWidth=260,
                                            callback=self.set_SourcePosition, sendSelectedValue=False, orientation="horizontal")

        self.source_position_box = oasysgui.widgetBox(main_box, "", addSpace=True, orientation="vertical", height=70)
        self.source_position_box_empty = oasysgui.widgetBox(main_box, "", addSpace=True, orientation="vertical", height=70)

        oasysgui.lineEdit(self.source_position_box, self, "z_origin", "Z Origin [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.source_position_box, self, "x_origin", "X Origin [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.source_position_box, self, "theta", "Theta [deg]", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_SourcePosition()

    def set_SourcePosition(self):
        self.source_position_box.setVisible(self.source_position == 0)
        self.source_position_box_empty.setVisible(self.source_position == 1)

    def check_fields(self):
        self.source_lambda = congruence.checkStrictlyPositiveNumber(self.source_lambda, "Wavelength")
        self.source_sigma = congruence.checkStrictlyPositiveNumber(self.source_sigma, "Sigma")
        self.theta = congruence.checkAngle(self.theta, "Theta")

    def do_wise_calculation(self):
        if self.source_position == 1:
            self.z_origin = 0.0
            self.x_origin = 0.0
            self.theta    = 0.0

        wise_inner_source = Optics.GaussianSource_1d(self.source_lambda,
                                                     self.source_sigma * numpy.sqrt(2),
                                                     ZOrigin = self.z_origin,
                                                     YOrigin =  self.x_origin,
                                                     Theta = self.theta)

        data_to_plot = numpy.zeros((2, 100))

        data_to_plot[0, :] = self.z_origin + (-5*self.source_sigma) + numpy.arange(100)*(self.source_sigma*0.1)
        data_to_plot[1, :] = (1/(self.source_sigma*numpy.sqrt(2*numpy.pi)))*numpy.exp(-0.5*(((data_to_plot[0, :]-self.z_origin)/self.source_sigma)**2))

        return wise_inner_source, data_to_plot

    def getTitles(self):
        return ["Gaussian Source Shape"]

    def getXTitles(self):
        return ["Z [m]"]

    def getYTitles(self):
        return ["Intensity [arbitrary units]"]

    def extract_plot_data_from_calculation_output(self, calculation_output):
        return calculation_output[1]

    def extract_wise_output_from_calculation_output(self, calculation_output):
        wise_source = WiseSource(inner_wise_source=calculation_output[0])
        wise_source.set_property("source_on_mirror_focus", self.source_position == 1)

        return WiseOutput(source=wise_source)

