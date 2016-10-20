import sys
from PyMca5.PyMcaGui.plotting.PlotWindow import PlotWindow

from PyQt4 import QtGui
from PyQt4.QtCore import QRect
from PyQt4.QtGui import QApplication

from orangewidget import gui
from orangewidget.settings import Setting
from orangewidget.widget import OWAction
from oasys.widgets import widget
from oasys.widgets import gui as oasysgui

from orangecontrib.wise.util.wise_util import EmittingStream, WisePlot
from orangecontrib.wise.util.wise_objects import WiseOutput

class WiseWidget(widget.OWWidget):
    author = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi@elettra.eu"

    outputs = [{"name": "wise_output",
                "type": WiseOutput,
                "doc": ""}]

    IMAGE_WIDTH = 760
    IMAGE_HEIGHT = 545
    MAX_WIDTH = 1320
    MAX_HEIGHT = 700
    CONTROL_AREA_WIDTH = 405
    TABS_AREA_HEIGHT = 560

    is_automatic_run = Setting(False)

    view_type=Setting(1)

    calculated_data = None
    plot_data = None

    want_main_area = 1

    def __init__(self):
        super().__init__()

        self.runaction = OWAction("Compute", self)
        self.runaction.triggered.connect(self.compute)
        self.addAction(self.runaction)

        geom = QApplication.desktop().availableGeometry()
        self.setGeometry(QRect(round(geom.width()*0.05),
                               round(geom.height()*0.05),
                               round(min(geom.width()*0.98, self.MAX_WIDTH)),
                               round(min(geom.height()*0.95, self.MAX_HEIGHT))))

        self.setMaximumHeight(self.geometry().height())
        self.setMaximumWidth(self.geometry().width())

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        self.general_options_box = gui.widgetBox(self.controlArea, "General Options", addSpace=True, orientation="horizontal")
        gui.checkBox(self.general_options_box, self, 'is_automatic_run', 'Automatic Execution')

        self.button_box = gui.widgetBox(self.controlArea, "", orientation="horizontal")
        #widget buttons: compute, set defaults, help
        gui.button(self.button_box, self, "Compute", callback=self.compute, height=35)
        gui.button(self.button_box, self, "Defaults", callback=self.defaults, height=35)

        gui.separator(self.controlArea, height=10)

        self.build_gui()

        gui.rubber(self.controlArea)

        self.main_tabs = gui.tabWidget(self.mainArea)
        plot_tab = gui.createTabPage(self.main_tabs, "Results")
        out_tab = gui.createTabPage(self.main_tabs, "Output")

        self.view_box = oasysgui.widgetBox(plot_tab, "Results Options", addSpace=False, orientation="horizontal")
        view_box_1 = oasysgui.widgetBox(self.view_box, "", addSpace=False, orientation="vertical", width=350)

        self.view_type_combo = gui.comboBox(view_box_1, self, "view_type", label="View Results",
                                            labelWidth=220,
                                            items=["No", "Yes"],
                                            callback=self.set_ViewType, sendSelectedValue=False, orientation="horizontal")

        self.tab = []
        self.tabs = gui.tabWidget(plot_tab)

        self.initializeTabs()

        self.wise_output = QtGui.QTextEdit()
        self.wise_output.setReadOnly(True)

        out_box = gui.widgetBox(out_tab, "System Output", addSpace=True, orientation="horizontal")
        out_box.layout().addWidget(self.wise_output)

        self.wise_output.setFixedHeight(600)
        self.wise_output.setFixedWidth(600)

        gui.rubber(self.mainArea)

    def build_gui(self):
        pass

    def initializeTabs(self):
        size = len(self.tab)
        indexes = range(0, size)

        for index in indexes:
            self.tabs.removeTab(size-1-index)

        titles = self.getTabTitles()

        self.tab = []
        self.plot_canvas = []

        for index in range(0, len(titles)):
            self.tab.append(gui.createTabPage(self.tabs, titles[index]))
            self.plot_canvas.append(None)

        for tab in self.tab:
            tab.setFixedHeight(self.IMAGE_HEIGHT)
            tab.setFixedWidth(self.IMAGE_WIDTH)

    def getTabTitles(self):
        return ["Calculation Result"]

    def getTitles(self):
        return ["Calculation Result"]

    def getXTitles(self):
        return ["Energy [eV]"]

    def getYTitles(self):
        return ["X [$\mu$m]"]

    def getVariablesToPlot(self):
        return [(0, 1)]

    def getLogPlot(self):
        return [(False, False)]

    def set_ViewType(self):
        self.progressBarInit()

        if not self.plot_data==None:
            try:
                self.initializeTabs()

                self.plot_results(self.plot_data)
            except Exception as exception:
                QtGui.QMessageBox.critical(self, "Error",
                                           str(exception),
                    QtGui.QMessageBox.Ok)

        self.progressBarFinished()

    def plot_results(self, plot_data, progressBarValue=80):
        if not self.view_type == 0:
            if not plot_data is None:
                self.view_type_combo.setEnabled(False)

                titles = self.getTitles()
                xtitles = self.getXTitles()
                ytitles = self.getYTitles()

                progress_bar_step = (100-progressBarValue)/len(titles)

                for index in range(0, len(titles)):
                    x_index, y_index = self.getVariablesToPlot()[index]
                    log_x, log_y = self.getLogPlot()[index]

                    try:
                        self.plot_histo(plot_data[x_index, :],
                                        plot_data[y_index, :],
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

    def writeStdOut(self, text):
        cursor = self.wise_output.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        self.wise_output.setTextCursor(cursor)
        self.wise_output.ensureCursorVisible()

    def plot_histo(self, x, y, progressBarValue, tabs_canvas_index, plot_canvas_index, title="", xtitle="", ytitle="", log_x=False, log_y=False):
        if self.plot_canvas[plot_canvas_index] is None:
            self.plot_canvas[plot_canvas_index] = PlotWindow(roi=False, control=True, position=True, plugins=False)
            self.plot_canvas[plot_canvas_index].setDefaultPlotLines(True)
            self.plot_canvas[plot_canvas_index].setActiveCurveColor(color='darkblue')
            self.plot_canvas[plot_canvas_index].setXAxisLogarithmic(log_x)
            self.plot_canvas[plot_canvas_index].setYAxisLogarithmic(log_y)

            self.tab[tabs_canvas_index].layout().addWidget(self.plot_canvas[plot_canvas_index])

        WisePlot.plot_histo(self.plot_canvas[plot_canvas_index], x, y, title, xtitle, ytitle)

        self.progressBarSet(progressBarValue)


    def compute(self):
        self.setStatusMessage("Running XOPPY")

        self.progressBarInit()

        try:
            sys.stdout = EmittingStream(textWritten=self.writeStdOut)

            self.progressBarSet(20)

            self.check_fields()

            calculation_output = self.do_wise_calculation()

            self.progressBarSet(50)

            if calculation_output is None:
                raise Exception("Wise gave no result")
            else:
                self.setStatusMessage("Plotting Results")

                self.plot_data = self.extract_plot_data_from_calculation_output(calculation_output)

                self.plot_results(self.plot_data, progressBarValue=60)

                self.setStatusMessage("")

                wise_output = self.extract_wise_output_from_calculation_output(calculation_output)
                if not wise_output is None: self.send("wise_output", wise_output)

        except Exception as exception:
            QtGui.QMessageBox.critical(self, "Error",
                                       str(exception), QtGui.QMessageBox.Ok)

            self.setStatusMessage("Error!")

            #raise exception

        self.progressBarFinished()


    def defaults(self):
         self.resetSettings()

    def check_fields(self):
        raise Exception("This method should be reimplementd in subclasses!")

    def do_wise_calculation(self):
        raise Exception("This method should be reimplementd in subclasses!")

    def extract_plot_data_from_calculation_output(self, calculation_output):
        raise Exception("This method should be reimplementd in subclasses!")

    def extract_wise_output_from_calculation_output(self, calculation_output):
        raise Exception("This method should be reimplementd in subclasses!")

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = WiseWidget()
    ow.show()
    a.exec_()
    ow.saveSettings()
