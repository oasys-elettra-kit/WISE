import numpy
from orangewidget import gui
from oasys.widgets import gui as oasysgui

from oasys.widgets import widget

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QRect

from orangewidget.settings import Setting

from wofry.propagator.wavefront1D.generic_wavefront import GenericWavefront1D

from wofrywise.propagator.wavefront1D.wise_wavefront import WiseWavefront

from orangecontrib.wise.util.wise_objects import WiseOutput, WiseNumericalIntegrationParameters
from orangecontrib.wise.util.wise_propagator import WisePropagatorsChain, WisePropagationAlgorithms, WisePropagationParameters

class OWWiseSourceToWofryWavefront1d(widget.OWWidget):
    name = "Wise Wavefront To Wofry Wavefront 1D"
    id = "toWofryWavefront1D"
    description = "Wise Wavefront To Wofry Wavefront 1D"
    icon = "icons/wf_to_wofry_wavefront_1d.png"
    priority = 3
    category = ""
    keywords = ["wise", "gaussian"]

    inputs = [("WiseOutput", WiseOutput, "set_input")]

    outputs = [{"name":"GenericWavefront1D",
                "type":GenericWavefront1D,
                "doc":"GenericWavefront1D",
                "id":"GenericWavefront1D"}]

    CONTROL_AREA_WIDTH = 405

    want_main_area = 0

    number_of_points = Setting(500)
    area_size = Setting(50.0)
    defocus_sweep = Setting(0.0)

    def __init__(self):
        super().__init__()

        geom = QApplication.desktop().availableGeometry()
        self.setGeometry(QRect(round(geom.width()*0.05),
                               round(geom.height()*0.05),
                               round(min(geom.width()*0.98, self.CONTROL_AREA_WIDTH+15)),
                               round(min(geom.height()*0.95, 125))))

        self.setMinimumHeight(self.geometry().height())
        self.setMinimumWidth(self.geometry().width())
        self.setMaximumHeight(self.geometry().height())
        self.setMaximumWidth(self.geometry().width())

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        main_box = oasysgui.widgetBox(self.controlArea, "WISE Wavefront to Wofry Wavefront Converter", orientation="vertical", width=self.CONTROL_AREA_WIDTH-5, height=100)

        oasysgui.lineEdit(main_box, self, "area_size", "Area Size [" + u"\u03BC" + "m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(main_box, self, "number_of_points", "Number of Points", labelWidth=260, valueType=int, orientation="horizontal")
        self.le_defocus_sweep = oasysgui.lineEdit(main_box, self, "defocus_sweep", "Defocus sweep", labelWidth=260, valueType=float, orientation="horizontal")

    def after_change_workspace_units(self):
        label = self.le_defocus_sweep.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")

    def set_input(self, input_data):
        self.setStatusMessage("")

        if not input_data is None:
            try:
                if input_data.has_wavefront():

                    detector_size = self.area_size*1e-6
                    number_of_points = self.number_of_points

                    previous_numerical_integration_parameters = input_data.get_numerical_integration_parameters()
                    numerical_integration_parameters = WiseNumericalIntegrationParameters(WiseNumericalIntegrationParameters.USER_DEFINED, detector_size, number_of_points)

                    propagation_type = WisePropagationParameters.MIRROR_AND_DETECTOR

                    #
                    # No need to recalculated wavefront on previous mirror surface
                    # if numerical integration parameters are identical
                    #
                    if WiseNumericalIntegrationParameters.USER_DEFINED == previous_numerical_integration_parameters.calculation_type:
                        if self.number_of_points == previous_numerical_integration_parameters.number_of_points:
                            propagation_type = WisePropagationParameters.DETECTOR_ONLY
                            numerical_integration_parameters.calculated_number_of_points = previous_numerical_integration_parameters.calculated_number_of_points

                    propagation_parameter = WisePropagationParameters(propagation_type=propagation_type,
                                                                      source=input_data.get_source().inner_wise_source,
                                                                      optical_element=input_data.get_optical_element().inner_wise_optical_element,
                                                                      wavefront=input_data.get_wavefront(),
                                                                      numerical_integration_parameters=numerical_integration_parameters,
                                                                      defocus_sweep=self.defocus_sweep * self.workspace_units_to_m)

                    propagation_output = WisePropagatorsChain.Instance().do_propagation(propagation_parameter,
                                                                                        WisePropagationAlgorithms.HuygensIntegral)

                    wavefront = WiseWavefront(wavelength=input_data.get_source().inner_wise_source.Lambda,
                                              positions=propagation_output.det_s,
                                              electric_fields=propagation_output.electric_fields,
                                              residuals=numpy.zeros(self.number_of_points))

                    self.send("GenericWavefront1D", wavefront.toGenericWavefront())
                else:
                    raise ValueError("No wavefront is present in input data")
            except Exception as exception:
                QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

                #raise exception
