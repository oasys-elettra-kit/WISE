import sys
import numpy
from PyQt4.QtGui import QApplication, QPalette, QColor, QFont, QMessageBox
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from orangecontrib.wise.util.wise_objects import WiseOpticalElement, WiseWavefront, WiseOutput, WisePreInputData, WiseNumericalIntegrationParameters
from orangecontrib.wise.widgets.gui.ow_wise_widget import WiseWidget
from orangecontrib.wise.util.wise_propagator import WisePropagatorsChain, WisePropagationAlgorithms, WisePropagationParameters

from wiselib import Optics
from  wiselib.Rayman import Amp, Cyc

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
    calculation_type = Setting(0)
    number_of_points = Setting(0)
    detector_size = Setting(50)
    calculated_number_of_points = 0

    input_data = None

    def set_input(self, input_data):
        self.setStatusMessage("")

        if not input_data is None:
            if input_data.has_optical_element():
                QMessageBox.critical(self, "Error", "Propagation from previous O.E. not yet supported", QMessageBox.Ok)

                self.setStatusMessage("Error!")

            self.input_data = input_data

            if self.is_automatic_run: self.compute()

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

        figure_error_box = oasysgui.widgetBox(self.controlArea, "Figure Error Parameters", orientation="vertical", width=self.CONTROL_AREA_WIDTH-5)


        gui.comboBox(figure_error_box, self, "use_figure_error", label="Error Profile",
                     items=["None", "User Defined"], labelWidth=260,
                     callback=self.set_UseFigureError, sendSelectedValue=False, orientation="horizontal")

        self.use_figure_error_box = oasysgui.widgetBox(figure_error_box, "", addSpace=True, orientation="vertical", height=70)
        self.use_figure_error_box_empty = oasysgui.widgetBox(figure_error_box, "", addSpace=True, orientation="vertical", height=70)


        file_box =  oasysgui.widgetBox(self.use_figure_error_box, "", addSpace=False, orientation="horizontal")
        self.le_figure_error_file = oasysgui.lineEdit(file_box, self, "figure_error_file", "File Name", labelWidth=100, valueType=str, orientation="horizontal")
        gui.button(file_box, self, "...", callback=self.selectFigureErrorFile)

        self.le_figure_error_step = oasysgui.lineEdit(self.use_figure_error_box, self, "figure_error_step", "Step", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.use_figure_error_box, self, "figure_error_um_conversion", "user file u.m. to [m] factor", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_UseFigureError()

        gui.comboBox(figure_error_box, self, "use_roughness", label="roughness",
                     items=["None", "User Defined"], labelWidth=260,
                     callback=self.set_UseRoughness, sendSelectedValue=False, orientation="horizontal")

        self.use_roughness_box = oasysgui.widgetBox(figure_error_box, "", addSpace=True, orientation="vertical", height=100)
        self.use_roughness_box_empty = oasysgui.widgetBox(figure_error_box, "", addSpace=True, orientation="vertical", height=100)

        file_box = oasysgui.widgetBox(self.use_roughness_box, "", addSpace=False, orientation="horizontal")
        self.le_roughness_file = oasysgui.lineEdit(file_box, self, "roughness_file", "File Name", labelWidth=100, valueType=str, orientation="horizontal")
        gui.button(file_box, self, "...", callback=self.selectroughnessFile)

        oasysgui.lineEdit(self.use_roughness_box, self, "roughness_x_scaling", "x user file u.m. to [m]   factor", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.use_roughness_box, self, "roughness_y_scaling", "y user file u.m. to [m^3] factor", labelWidth=260, valueType=float, orientation="horizontal")

        gui.comboBox(self.use_roughness_box, self, "roughness_fit_data", label="Fit numeric data with power law",
                     items=["No", "Yes"], labelWidth=260, sendSelectedValue=False, orientation="horizontal")

        self.set_UseRoughness()

        calculation_box = oasysgui.widgetBox(self.controlArea, "Calculation Parameters", orientation="vertical", width=self.CONTROL_AREA_WIDTH-5)

        gui.comboBox(calculation_box, self, "calculation_type", label="Numeric Integration",
                     items=["Automatic Number of Points", "User Defined Number of Points"], labelWidth=160,
                     callback=self.set_CalculationType, sendSelectedValue=False, orientation="horizontal")


        self.detector_box = oasysgui.widgetBox(calculation_box, "", orientation="vertical", width=self.CONTROL_AREA_WIDTH-25)

        oasysgui.lineEdit(self.detector_box, self, "detector_size", "(Hypotetic) Detector Size [" + u"\u03BC" + "m]", labelWidth=260, valueType=float, orientation="horizontal")

        le_calculated_number_of_points = oasysgui.lineEdit(self.detector_box, self, "calculated_number_of_points", "Calculated Number of Points", labelWidth=260, valueType=float, orientation="horizontal")
        le_calculated_number_of_points.setReadOnly(True)
        font = QFont(le_calculated_number_of_points.font())
        font.setBold(True)
        le_calculated_number_of_points.setFont(font)
        palette = QPalette(le_calculated_number_of_points.palette())
        palette.setColor(QPalette.Text, QColor('dark blue'))
        palette.setColor(QPalette.Base, QColor(243, 240, 160))
        le_calculated_number_of_points.setPalette(palette)

        self.number_box = oasysgui.widgetBox(calculation_box, "", orientation="vertical", width=self.CONTROL_AREA_WIDTH-25)

        oasysgui.lineEdit(self.number_box, self, "number_of_points", "Number of Points", labelWidth=260, valueType=int, orientation="horizontal")

        self.set_CalculationType()

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

    def set_CalculationType(self):
        self.detector_box.setVisible(self.calculation_type==0)
        self.number_box.setVisible(self.calculation_type==1)

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

        if self.calculation_type == 0: #auto
            self.detector_size = congruence.checkStrictlyPositiveNumber(self.detector_size, "Detector Size")
        else:
            self.number_of_points = congruence.checkStrictlyPositiveNumber(self.number_of_points, "Number of Points")

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

        source = self.input_data.get_source()

        if source.get_property("source_on_mirror_focus"):
            longitudinal_correction = float(source.get_property("longitudinal_correction"))
            transverse_correction   = float(source.get_property("transverse_correction"))
            delta_theta             = numpy.radians(float(source.get_property("delta_theta")))

            if longitudinal_correction == 0.0:
                if transverse_correction == 0.0:
                    alpha = 0
                else:
                    alpha = elliptic_mirror.p1_Angle + numpy.sign(transverse_correction)*numpy.pi/2
            else:
                alpha = elliptic_mirror.p1_Angle + numpy.arctan(transverse_correction/longitudinal_correction)

            defocus = numpy.sqrt(longitudinal_correction**2 + transverse_correction**2)

            theta = elliptic_mirror.p1_Angle + delta_theta
            z_origin = elliptic_mirror.XYF1[0] + defocus*numpy.cos(alpha)
            y_origin = elliptic_mirror.XYF1[1] + defocus*numpy.sin(alpha)

            print(numpy.degrees(theta), z_origin, y_origin)

            source.inner_wise_source = Optics.GaussianSource_1d(source.inner_wise_source.Lambda,
                                                                source.inner_wise_source.Waist0,
                                                                ZOrigin=z_origin,
                                                                YOrigin=y_origin,
                                                                Theta=theta)

        if self.calculation_type == WiseNumericalIntegrationParameters.AUTOMATIC:
            detector_size = self.detector_size*1e-6
            number_of_points = -1
        else:
            detector_size = 0.0
            number_of_points = self.number_of_points

        numerical_integration_parameters = WiseNumericalIntegrationParameters(self.calculation_type, detector_size, number_of_points)

        propagation_parameter = WisePropagationParameters(propagation_type=WisePropagationParameters.MIRROR_ONLY,
                                                          source=source.inner_wise_source,
                                                          optical_element=elliptic_mirror,
                                                          numerical_integration_parameters=numerical_integration_parameters)

        propagation_output = WisePropagatorsChain.Instance().do_propagation(propagation_parameter,
                                                                            WisePropagationAlgorithms.HuygensIntegral)


        if self.calculation_type == WiseNumericalIntegrationParameters.AUTOMATIC:
            self.calculated_number_of_points = propagation_output.number_of_points
        else:
            self.calculated_number_of_points = 0

        wavefront_out = WiseWavefront(propagation_output.mir_x,
                                      propagation_output.mir_y,
                                      propagation_output.mir_s,
                                      propagation_output.mir_E,
                                      propagation_output.residuals)


        numerical_integration_parameters_out = WiseNumericalIntegrationParameters(self.calculation_type,
                                                                                  detector_size,
                                                                                  number_of_points,
                                                                                  propagation_output.number_of_points)

        optical_element_out = WiseOpticalElement(inner_wise_optical_element=elliptic_mirror)

        data_to_plot = numpy.zeros((5, len(propagation_output.mir_s)))
        data_to_plot[0, :] = propagation_output.mir_s / self.workspace_units_to_m
        data_to_plot[1, :] = Amp(propagation_output.mir_E)**2
        data_to_plot[2, :] = Cyc(propagation_output.mir_E)

        if len(propagation_output.residuals) > 0:
            figure_error_x = numpy.linspace(0, self.length, len(propagation_output.residuals))
            data_to_plot_fe = numpy.zeros((2, len(figure_error_x)))

            data_to_plot_fe[0, :] = figure_error_x
            data_to_plot_fe[1, :] = propagation_output.residuals*1e9 # nm
        else:
            data_to_plot_fe = numpy.zeros((2, 1))

            data_to_plot_fe[0, :] = numpy.zeros(1)
            data_to_plot_fe[1, :] = numpy.zeros(1)

        return source, optical_element_out, wavefront_out, numerical_integration_parameters_out, data_to_plot, data_to_plot_fe

    def getTabTitles(self):
        return ["Field Intensity (mirror)", "Optical Cycles (mirror)", "Figure Error"]

    def getTitles(self):
        return ["Field Intensity (mirror)", "Optical Cycles (mirror)", "Figure Error"]

    def getXTitles(self):
        return ["rho [" + self.workspace_units_label + "]", "Z [" + self.workspace_units_label + "]", "Z [$\mu$m]"]

    def getYTitles(self):
        return ["|E0|**2", "Optical Cycles", "Height Error [nm]"]

    def getVariablesToPlot(self):
        return [(0, 1), (0, 2), (0, 1)]

    def getLogPlot(self):
        return [(False, False), (False, False), (False, False)]

    def extract_plot_data_from_calculation_output(self, calculation_output):
        return calculation_output[4], calculation_output[5]


    def plot_results(self, plot_data, progressBarValue=80):
        if not self.view_type == 0:
            if not plot_data is None:

                plot_data_1 = plot_data[0]
                plot_data_2 = plot_data[1]

                self.view_type_combo.setEnabled(False)

                titles = self.getTitles()
                xtitles = self.getXTitles()
                ytitles = self.getYTitles()

                progress_bar_step = (100-progressBarValue)/len(titles)

                for index in range(0, len(titles)):
                    x_index, y_index = self.getVariablesToPlot()[index]
                    log_x, log_y = self.getLogPlot()[index]

                    try:
                        if index < 2:
                            self.plot_histo(plot_data_1[x_index, :],
                                            plot_data_1[y_index, :],
                                            progressBarValue + ((index+1)*progress_bar_step),
                                            tabs_canvas_index=index,
                                            plot_canvas_index=index,
                                            title=titles[index],
                                            xtitle=xtitles[index],
                                            ytitle=ytitles[index],
                                            log_x=log_x,
                                            log_y=log_y)
                        else:
                            self.plot_histo(plot_data_2[x_index, :],
                                            plot_data_2[y_index, :],
                                            progressBarValue + ((index+1)*progress_bar_step),
                                            tabs_canvas_index=index,
                                            plot_canvas_index=index,
                                            title=titles[index],
                                            xtitle=xtitles[index],
                                            ytitle=ytitles[index],
                                            log_x=log_x,
                                            log_y=log_y)

                        self.tabs.setCurrentIndex(index)
                    except Exception as e:
                        self.view_type_combo.setEnabled(True)

                        raise Exception("Data not plottable: bad content\n" + str(e))

                self.view_type_combo.setEnabled(True)
            else:
                raise Exception("Empty Data")


    def extract_wise_output_from_calculation_output(self, calculation_output):
        return WiseOutput(source=calculation_output[0],
                          optical_element=calculation_output[1],
                          wavefront=calculation_output[2],
                          numerical_integration_parameters=calculation_output[3])
