
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets, QtGui

class MainWindow(object):
    def __init__(self):
        self.app = pg.mkQApp("BumpBlaster5000 Interface")
        
        
        self.layout = pg.LayoutWidget()
        self.set_palette()
        
        # number of slices
        self._num_slices_label = QtWidgets.QLabel()
        self._num_slices_label.setText("Number of Slices:")
        self.num_slices_input = QtWidgets.QLineEdit()
        
        # begin read raw data stream
        self.start_rrds_button = QtWidgets.QPushButton("Begin ReadRawDataStream")
        
        # ch 1 viewing
        self.ch1_set_active = QtWidgets.QCheckBox("Ch1 Active")
        
        self._ch1_num_stacks_label = QtWidgets.QLabel()
        self._ch1_num_stacks_label.setText("Frames to average:")  
        self.ch1_num_stacks_input = QtWidgets.QLineEdit()
        
        self.ch1_plot = pg.PlotWidget(title = "Ch1")
        
        self.ch1_freeze_button = QtWidgets.QCheckBox("Freeze Image")
        
        
        # ch2 viewing
        self.ch2_set_active = QtWidgets.QCheckBox("Ch2 Active")
        self._ch2_num_stacks_label = QtWidgets.QLabel()
        self._ch2_num_stacks_label.setText("Frames to average:")
        self.ch2_num_stacks_input = QtWidgets.QLineEdit()
        
        self.ch2_plot = pg.PlotWidget(title = "Ch2")
        
        self.ch2_freeze_button = QtWidgets.QCheckBox("Freeze Image")
        
        # ROI buttons
        self.load_eb_roi_button = QtWidgets.QPushButton("Load EB ROIs")
        self.load_pb_roi_button = QtWidgets.QPushButton("Load PB ROIs")
        
        self.clear_roi_button = QtWidgets.QPushButton("Clear ROIs")
        
        self.lock_roi_checkbox = QtWidgets.QCheckBox("Lock ROIs")
        
        
        # Bump calculation buttons
        self._func_ch_label = QtWidgets.QLabel()
        self._func_ch_label.setText("Functional Channel:")
        
        self.func_ch1_button = QtWidgets.QRadioButton("Ch1")
        self.func_ch2_button = QtWidgets.QRadioButton("Ch2")
        
        self._func_nframes_avg_label = QtWidgets.QLabel()
        self._func_nframes_avg_label.setText("Func Frames to Average:")
        self.func_nframes_avg_input = QtWidgets.QLineEdit()
        
        self._base_ch_label = QtWidgets.QLabel()
        self._base_ch_label.setText("Baseline Channel:")
        
        self.base_ch1_button = QtWidgets.QRadioButton("Ch1")
        self.base_ch2_button = QtWidgets.QRadioButton("Ch2")
        
        self._base_nframes_avg_label = QtWidgets.QLabel()
        self._base_nframes_avg_label.setText("Baseline Frames to Average:")
        self.base_nframes_avg_input = QtWidgets.QLineEdit()
        
        
        self.calc_bump_button = QtWidgets.QCheckBox("Calculate Bump")
        self.read_heading_button = QtWidgets.QCheckBox("Read VR Heading")
        
        self.remote_plot_button = QtWidgets.QCheckBox("Remote Plot")
        
        # bump plots
        self.bump_plot = pg.PlotWidget(title="Bump Dynamics")
        self.offset_plot = pg.PlotWidget(title = "Bump Offset Histogram")
        
        self.set_layout()
        self.layout.show()

        
    def set_layout(self):
        self.layout.addWidget(self._num_slices_label,row=0, col=0)
        self.layout.addWidget(self.num_slices_input, row=0, col=1)
        self.layout.addWidget(self.start_rrds_button, row=0, col=2)
        
        self.layout.addWidget(self.ch1_set_active, row=1, col=0, colspan=2)
        self.layout.addWidget(self._ch1_num_stacks_label,row=2, col=0)
        self.layout.addWidget(self.ch1_num_stacks_input, row=2, col=1)
        self.layout.addWidget(self.ch1_freeze_button, row=3,col=0)
        self.layout.addWidget(self.ch1_plot, row=1, col=2, colspan=4, rowspan=4)
        
        self.layout.addWidget(self.ch2_set_active, row=1, col=6, colspan=2)
        self.layout.addWidget(self._ch2_num_stacks_label,row=2, col=6)
        self.layout.addWidget(self.ch2_num_stacks_input, row=2, col=7)
        self.layout.addWidget(self.ch2_freeze_button, row=3,col=6)
        self.layout.addWidget(self.ch2_plot, row=1, col=8, colspan=4, rowspan=4)
        
        self.layout.addWidget(self.load_eb_roi_button, row=5, col=0, colspan=1)
        self.layout.addWidget(self.load_pb_roi_button, row=5, col=1, colspan=1)
        self.layout.addWidget(self.clear_roi_button, row=5, col=4, colspan=1)
        self.layout.addWidget(self.lock_roi_checkbox, row=5, col=3, colspan=1)
        
        self.layout.addWidget(self._func_ch_label, row=6, col=0)
        self.layout.addWidget(self.func_ch1_button, row=6, col=1)
        self.layout.addWidget(self.func_ch2_button, row=6, col=2)
        self.layout.addWidget(self._func_nframes_avg_label, row=6, col=3)
        self.layout.addWidget(self.func_nframes_avg_input, row=6, col=4)
        
        self.layout.addWidget(self._base_ch_label, row=7, col=0)
        self.layout.addWidget(self.base_ch1_button, row=7, col=1)
        self.layout.addWidget(self.base_ch2_button, row=7, col=2)
        self.layout.addWidget(self._base_nframes_avg_label, row=7, col=3)
        self.layout.addWidget(self.base_nframes_avg_input, row=7, col=4)
        
        self.layout.addWidget(self.calc_bump_button, row=6, col=8)
        self.layout.addWidget(self.read_heading_button, row=6, col=9)
        self.layout.addWidget(self.remote_plot_button, row=6, col=10)
        
        self.layout.addWidget(self.bump_plot, row=8, col=0, rowspan=3, colspan=7)
        self.layout.addWidget(self.offset_plot, row=8, col=8, rowspan=3, colspan=4)
        
        for col in range(12):
            self.layout.layout.setColumnStretch(col,1)
        for row in range(9):
            self.layout.layout.setRowStretch(row,1)
        
        self.layout.resize(1200,700)
        
        
    def set_palette(self):
        # set color scheme
        palette = QtGui.QPalette()
        # background
        brush = QtGui.QBrush(QtGui.QColor(36,31,49,255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Window,brush)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Window,brush)
        # window text
        brush = QtGui.QBrush(QtGui.QColor(216, 216, 216))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.WindowText, brush)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.WindowText, brush)
        # push buttons
        brush = QtGui.QBrush(QtGui.QColor(5, 77, 72))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Button, brush)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Button, brush)
        brush = QtGui.QBrush(QtGui.QColor(77, 77, 77, 122))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Button, brush)
        self.layout.setPalette(palette)
        
class RemotePlottingWindow(object):
    
    def __init__(self):
        self.app = pg.mkQApp("Remote Plotting Window")
        
        self.layout = pg.LayoutWidget()
        self.set_palette()
        
        # plots 
        self.ch1_plot = pg.PlotWidget(title="Ch1")
        self.ch2_plot = pg.PlotWidget(title="Ch2")
        self.bump_plot = pg.PlotWidget(title="BumpPlot")
        self.offset_plot = pg.PlotWidget(title="Offset Histogram")
        
        
        
        self.layout.addWidget(self.ch1_plot,row=0, col=0, rowspan=1, colspan=3)
        self.layout.addWidget(self.ch2_plot,row=0, col=3, rowspan=1, colspan=3)
        self.layout.addWidget(self.bump_plot,row=1, col=0, colspan=4, rowspan=1)
        self.layout.addWidget(self.offset_plot, row=1, col=4,colspan=2)
        
        
        for col in range(6):
            self.layout.layout.setColumnStretch(col,2)
        self.layout.layout.setRowStretch(0,2)
        self.layout.layout.setRowStretch(1,1)
        
        
        self.ch2_plot.setXLink(self.ch1_plot)
        self.bump_plot.setXLink(self.ch1_plot)
        self.bump_plot.setXLink(self.ch1_plot)
        
        self.layout.resize(1000,600)
        self.layout.show()
        
    def set_palette(self):
        # set color scheme
        palette = QtGui.QPalette()
        # background
        brush = QtGui.QBrush(QtGui.QColor(36,31,49,255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Window,brush)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Window,brush)
        # window text
        brush = QtGui.QBrush(QtGui.QColor(216, 216, 216))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.WindowText, brush)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.WindowText, brush)
        # push buttons
        brush = QtGui.QBrush(QtGui.QColor(5, 77, 72))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Button, brush)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Button, brush)
        brush = QtGui.QBrush(QtGui.QColor(77, 77, 77, 122))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Button, brush)
        self.layout.setPalette(palette)
        
        
        
if __name__ == '__main__':
    mw = MainWindow()
    rpw = RemotePlottingWindow()
    pg.exec()
