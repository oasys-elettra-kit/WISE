import numpy

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QRect

from orangewidget.settings import Setting
from orangewidget import gui

from oasys.widgets import gui as oasysgui
from oasys.widgets.widget import AutomaticWidget

from wofry.propagator.wavefront1D.generic_wavefront import GenericWavefront1D
from wofrywise.propagator.wavefront1D.wise_wavefront import WiseWavefront

from orangecontrib.wise.util.wise_objects import WiseOutput


class OWWiseSourceToWofryWavefront1d(AutomaticWidget):
    name = "Wise Source To Wofry Wavefront 1D"
    id = "toWofryWavefront1D"
    description = "Wise Source To Wofry Wavefront 1D"
    icon = "icons/source_to_wofry_wavefront_1d.png"
    priority = 2
    category = ""
    keywords = ["wise", "gaussian"]

    inputs = [("WiseOutput", WiseOutput, "set_input")]

    outputs = [{"name":"GenericWavefront1D",
                "type":GenericWavefront1D,
                "doc":"GenericWavefront1D",
                "id":"GenericWavefront1D"}]

    MAX_WIDTH = 420
    MAX_HEIGHT = 200
    CONTROL_AREA_WIDTH = 410

    want_main_area = 0

    number_of_points = Setting(500)
    
    source = None
    
    def __init__(self):
        super().__init__()

        geom = QApplication.desktop().availableGeometry()
        self.setGeometry(QRect(round(geom.width()*0.05),
                               round(geom.height()*0.05),
                               round(min(geom.width()*0.98, self.MAX_WIDTH)),
                               round(min(geom.height()*0.95, self.MAX_HEIGHT))))

        self.setMinimumHeight(self.geometry().height())
        self.setMinimumWidth(self.geometry().width())
        self.setMaximumHeight(self.geometry().height())
        self.setMaximumWidth(self.geometry().width())

        self.controlArea.setFixedWidth(self.MAX_WIDTH-10)
        self.controlArea.setFixedHeight(self.MAX_HEIGHT-10)


        main_box = oasysgui.widgetBox(self.controlArea, "WISE Source to Wofry Wavefront Converter", orientation="vertical", width=self.CONTROL_AREA_WIDTH-5, height=110)

        oasysgui.lineEdit(main_box, self, "number_of_points", "Number of Points", labelWidth=260, valueType=float, orientation="horizontal")

        gui.button(main_box, self, "Compute", height=40, callback=self.compute)

    def compute(self):
        if not self.source is None:
            try:
                self.source = self.input_data.get_self.source().inner_wise_self.source

                yy = numpy.linspace(-5*self.source.Waist0/numpy.sqrt(2) + self.source.ZOrigin,
                                    5*self.source.Waist0/numpy.sqrt(2) + self.source.ZOrigin,
                                    self.number_of_points)

                electric_fields = self.source.EvalField_XYSelf(numpy.zeros(self.number_of_points),
                                                          yy)

                source_wavefront = WiseWavefront(wavelength=self.source.Lambda,
                                                 positions=yy/self.workspace_units_to_m,
                                                 electric_fields=electric_fields,
                                                 residuals=numpy.zeros(self.number_of_points))

                self.send("GenericWavefront1D", source_wavefront.toGenericWavefront())
            except Exception as exception:
                QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

                #raise exception
        

    def set_input(self, input_data):
        self.setStatusMessage("")

        if not input_data is None:
            try:
                if input_data.has_source():
                    self.source = input_data.get_source().inner_wise_source
                    
                    if self.is_automatic_execution:
                        self.compute()
                else:
                    raise ValueError("No source is present in input data")
            except Exception as exception:
                QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

                #raise exception
