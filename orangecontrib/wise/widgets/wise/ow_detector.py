import sys
import numpy
from PyQt4.QtGui import QApplication, QPalette, QColor, QFont, QDialog

from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from orangecontrib.wise.util.wise_objects import WiseOpticalElement, Wavefront, WiseOutput
from orangecontrib.wise.widgets.gui.ow_wise_widget import WiseWidget

from wiselib import Optics
import wiselib.Rayman5 as Rayman
from  wiselib.Rayman5 import Amp, Cyc

class OWDetector(WiseWidget):
    name = "Detector"
    id = "Detector"
    description = "Detector"
    icon = "icons/detector.png"
    priority = 3
    category = ""
    keywords = ["wise", "elliptical"]

    inputs = [("Input", WiseOutput, "set_input")]
    outputs = []

    detector_size = 0.0
    oe_f2 = 0.0

    defocus_sweep = Setting(0.0)

    defocus_start = Setting(-10e-3)
    defocus_stop = Setting(10e-3)
    defocus_step = Setting(1e-3)

    use_multipool = Setting(0)
    n_pools = Setting(5)

    def set_input(self, input_data):
        self.input_data = input_data

        if not self.input_data.has_optical_elements():
            raise Exception("Detector can be collegated only after an Optical Element")

        optical_element = self.input_data.get_last_optical_element()

        self.detector_size = numpy.round(optical_element.get_property("detector_size")*1e6, 1)
        self.oe_f2         = optical_element.inner_wise_optical_element.f2

        self.compute()


    def build_gui(self):
        self.view_type = 1

        main_box = oasysgui.widgetBox(self.controlArea, "Detector Parameters", orientation="vertical", width=self.CONTROL_AREA_WIDTH-5)

        le_detector_size = oasysgui.lineEdit(main_box, self, "detector_size", "detector_size [" + u"\u03BC" + "m]", labelWidth=260, valueType=float, orientation="horizontal")
        le_detector_size.setReadOnly(True)
        font = QFont(le_detector_size.font())
        font.setBold(True)
        le_detector_size.setFont(font)
        palette = QPalette(le_detector_size.palette())
        palette.setColor(QPalette.Text, QColor('dark blue'))
        palette.setColor(QPalette.Base, QColor(243, 240, 160))
        le_detector_size.setPalette(palette)

        le_oe_f2 = oasysgui.lineEdit(main_box, self, "oe_f2", "O.E. F2 [m]", labelWidth=260, valueType=float, orientation="horizontal")
        le_oe_f2.setReadOnly(True)
        font = QFont(le_oe_f2.font())
        font.setBold(True)
        le_oe_f2.setFont(font)
        palette = QPalette(le_oe_f2.palette())
        palette.setColor(QPalette.Text, QColor('dark blue'))
        palette.setColor(QPalette.Base, QColor(243, 240, 160))
        le_oe_f2.setPalette(palette)

        oasysgui.lineEdit(main_box, self, "defocus_sweep", "Defocus sweep [m]", labelWidth=260, valueType=float, orientation="horizontal")

        best_focus_box = oasysgui.widgetBox(self.controlArea, "Best Focus Calculation", orientation="vertical", width=self.CONTROL_AREA_WIDTH-5)

        oasysgui.lineEdit(best_focus_box, self, "defocus_start", "Defocus sweep start [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(best_focus_box, self, "defocus_stop", "Defocus sweep stop [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(best_focus_box, self, "defocus_step", "Defocus sweep step [m]", labelWidth=260, valueType=float, orientation="horizontal")

        gui.comboBox(best_focus_box, self, "use_multipool", label="Use Parallel Processing",
                     items=["No", "Yes"], labelWidth=260,
                     callback=self.set_Multipool, sendSelectedValue=False, orientation="horizontal")

        self.use_multipool_box = oasysgui.widgetBox(best_focus_box, "", addSpace=True, orientation="vertical", height=30)
        self.use_multipool_box_empty = oasysgui.widgetBox(best_focus_box, "", addSpace=True, orientation="vertical", height=30)

        oasysgui.lineEdit(self.use_multipool_box, self, "n_pools", "Nr. Parallel Processes", labelWidth=260, valueType=int, orientation="horizontal")

        gui.button(best_focus_box, self, "Find Best Focus Position", callback=self.do_best_focus_calculation, height=35)

        self.set_Multipool()

    def set_Multipool(self):
        self.use_multipool_box.setVisible(self.use_multipool == 1)
        self.use_multipool_box_empty.setVisible(self.use_multipool == 0)

    def set_ViewType(self):
        self.view_type = 1

    def check_fields(self):
        if self.use_multipool == 1:
            self.n_pools = congruence.checkStrictlyPositiveNumber(self.n_pools, "Nr. Parallel Processes")

    def do_wise_calculation(self):
        if self.defocus_sweep == 0.0:
            wavefront = self.input_data.get_wavefront()

            data_to_plot = numpy.zeros((2, len(wavefront.positions)))
            data_to_plot[0, :] = wavefront.positions * 1e6
            data_to_plot[1, :] = Amp(wavefront.electric_fields)**2
        else:
            if self.oe_f2 + self.defocus_sweep <= 0: raise Exception("Defocus sweep reached the previous mirror")

            source =  self.input_data.get_source().inner_wise_source
            elliptic_mirror = self.input_data.get_last_optical_element().inner_wise_optical_element

            theta_0 = elliptic_mirror.pTan_Angle
            theta_1 = numpy.arctan(-1/elliptic_mirror.p2[0])
            det_size = self.input_data.get_last_optical_element().get_property("detector_size")
            n_auto = Rayman.SamplingCalculator(source.Lambda,
                                               elliptic_mirror.f2,
                                               elliptic_mirror.L,
                                               det_size,
                                               theta_0,
                                               theta_1)

            # Piano specchio (Sorgente=>Specchio)
            mir_x, mir_y = elliptic_mirror.GetXY_MeasuredMirror(n_auto, 0)
            mir_E = source.EvalField_XYLab(mir_x, mir_y)

            det_x, det_y = elliptic_mirror.GetXY_TransversePlaneAtF2(det_size, n_auto, self.defocus_sweep)
            det_s = Rayman.xy_to_s(det_x, det_y)

            electric_fields = Rayman.HuygensIntegral_1d_MultiPool(source.Lambda,
                                                                  mir_E,
                                                                  mir_x,
                                                                  mir_y,
                                                                  det_x,
                                                                  det_y,
                                                                  0)

            data_to_plot = numpy.zeros((5, n_auto))
            data_to_plot[0, :] = det_s * 1e6
            data_to_plot[1, :] = Amp(electric_fields)**2

        return data_to_plot

    def getTitles(self):
        return ["Intensity on Focus Position: " + str(numpy.round(self.oe_f2 + self.defocus_sweep, 6))]

    def getXTitles(self):
        return ["Z [$\mu$m]"]

    def getYTitles(self):
        return ["Intensity"]

    def getVariablesToPlot(self):
        return [(0, 1)]

    def getLogPlot(self):
        return [(False, False)]

    def extract_plot_data_from_calculation_output(self, calculation_output):
        return calculation_output

    def extract_wise_output_from_calculation_output(self, calculation_output):
        return None

    def do_best_focus_calculation(self):
        if self.defocus_start >= self.defocus_stop: raise Exception("Defocus sweep start must be < Defocus sweep stop")
        self.defocus_step = congruence.checkStrictlyPositiveNumber(self. defocus_step, "Defocus sweep step")
        if self.defocus_step >= self.defocus_stop - self.defocus_start: raise Exception("Defocus step is too big")

        source =  self.input_data.get_source().inner_wise_source
        elliptic_mirror = self.input_data.get_last_optical_element().inner_wise_optical_element

        theta_0 = elliptic_mirror.pTan_Angle
        theta_1 = numpy.arctan(-1/elliptic_mirror.p2[0])
        det_size = self.input_data.get_last_optical_element().get_property("detector_size")
        n_auto = Rayman.SamplingCalculator(source.Lambda,
                                           elliptic_mirror.f2,
                                           elliptic_mirror.L,
                                           det_size,
                                           theta_0,
                                           theta_1)

        if self.use_multipool == 0:
            n_pools = 0
        else:
            n_pools = self.n_pools

        # Piano specchio (Sorgente=>Specchio)
        mir_x, mir_y = elliptic_mirror.GetXY_MeasuredMirror(n_auto, 0)
        mir_E = source.EvalField_XYLab(mir_x, mir_y)

        defocus_list = numpy.arange(self.defocus_start, self.defocus_stop, self.defocus_step)

        n_defocus = len(defocus_list)

        E1_list = numpy.empty((n_defocus, n_auto) , dtype = complex)

        index_min = -1
        hew_min = numpy.inf

        for i, defocus in enumerate(defocus_list):
            print ('Processing %d/%d: Defocus = %0.1f mm' %(i, n_defocus, (defocus * 1e3)))
            # Specchio => Detector
            det_x, det_y = elliptic_mirror.GetXY_TransversePlaneAtF2(det_size, n_auto, defocus)
            det_ds = numpy.sqrt((det_x[0] - det_x[-1])**2 + (det_y[0] - det_y[-1])**2)

            # E1
            E1_list[i, :] = Rayman.HuygensIntegral_1d_MultiPool(source.Lambda,
                                                                mir_E,
                                                                mir_x,
                                                                mir_y,
                                                                det_x,
                                                                det_y,
                                                                n_pools)

            hew = Rayman.HalfEnergyWidth_1d(abs(E1_list[i, :])**2, Step = det_ds)

            if hew < hew_min:
                hew_min = hew
                index_min = i

        electric_fields = E1_list[index_min, :]
        new__fw = self.oe_f2 + defocus_list[index_min]
        det_x, det_y = elliptic_mirror.GetXY_TransversePlaneAtF2(det_size, n_auto, defocus_list[index_min])
        det_s = Rayman.xy_to_s(det_x, det_y)

        self.plot_histo(det_s * 1e6,
                        Amp(electric_fields)**2,
                        80,
                        tabs_canvas_index=0,
                        plot_canvas_index=0,
                        title="Intensity at Best Focus Position: " + str(new__fw),
                        xtitle="Z [$\mu$m]",
                        ytitle="Intensity",
                        log_x=False,
                        log_y=False)

        self.progressBarFinished()