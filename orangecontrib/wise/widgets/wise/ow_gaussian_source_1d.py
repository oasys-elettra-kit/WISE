import sys
import numpy
from PyQt4.QtGui import QApplication
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui

from orangecontrib.wise.util.wise_objects import WiseSource, WiseOutput
from orangecontrib.wise.widgets.gui.ow_wise_widget import WiseWidget

from wiselib import Optics

class OWGaussianSource1d(WiseWidget):
    name = "GaussianSource1d"
    id = "GaussianSource1d"
    description = "GaussianSource1d"
    icon = "icons/gaussian_source_1d.png"
    priority = 10
    category = ""
    keywords = ["wise", "gaussian"]

    TITLE = Setting("Thermal source: Planck distribution")
    TEMPERATURE = Setting(1200000.0)
    E_MIN = Setting(10.0)
    E_MAX = Setting(1000.0)
    NPOINTS = Setting(500)

    def build_gui(self):

        box = oasysgui.widgetBox(self.controlArea, "Gaussian Source 1D Input Parameters", orientation="vertical", width=self.CONTROL_AREA_WIDTH-5)


    def check_fields(self):
        raise Exception("This method should be reimplementd in subclasses!")

    def do_wise_calculation(self):
        raise Exception("This method should be reimplementd in subclasses!")

    def extract_plot_data_from_calculation_output(self, calculation_output):
        raise Exception("This method should be reimplementd in subclasses!")

    def extract_wise_output_from_calculation_output(self, calculation_output):
        raise Exception("This method should be reimplementd in subclasses!")
