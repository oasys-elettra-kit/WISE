__author__ = 'labx'

import sys
from PyQt4 import QtGui, QtCore

try:
    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib import cm
    from matplotlib import figure as matfig
    import pylab
except ImportError:
    print(sys.exc_info()[1])
    pass

class EmittingStream(QtCore.QObject):
    textWritten = QtCore.pyqtSignal(str)

    def write(self, text):
        self.textWritten.emit(str(text))

class ShowTextDialog(QtGui.QDialog):

    def __init__(self, title, text, width=650, height=400, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setModal(True)
        self.setWindowTitle(title)
        layout = QtGui.QVBoxLayout(self)

        text_edit = QtGui.QTextEdit(text, self)
        text_edit.setReadOnly(True)

        text_area = QtGui.QScrollArea(self)
        text_area.setWidget(text_edit)
        text_area.setWidgetResizable(True)
        text_area.setFixedHeight(height)
        text_area.setFixedWidth(width)

        bbox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok)

        bbox.accepted.connect(self.accept)
        layout.addWidget(text_area)
        layout.addWidget(bbox)

    @classmethod
    def show_text(cls, title, text, width=650, height=400, parent=None):
        dialog = ShowTextDialog(title, text, width, height, parent)
        dialog.show()

class WisePlot:

    @classmethod
    def plot_histo(cls, plot_window, x, y, title, xtitle, ytitle):
        matplotlib.rcParams['axes.formatter.useoffset']='False'

        plot_window.addCurve(x, y, title, symbol='', color='blue', replace=True) #'+', '^', ','
        if not xtitle is None: plot_window.setGraphXLabel(xtitle)
        if not ytitle is None: plot_window.setGraphYLabel(ytitle)
        if not title is None: plot_window.setGraphTitle(title)
        plot_window.setDrawModeEnabled(True, 'rectangle')
        plot_window.setZoomModeEnabled(True)
        plot_window.resetZoom()
        plot_window.replot()
