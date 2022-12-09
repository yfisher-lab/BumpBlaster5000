import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtGui, QtCore


class WidgetWindow:
    
    def __init__(self):
        self.app = pg.mkQApp("BumpBlaster5000 Interface")
        
        
        self.layout = pg.LayoutWidget()
        
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
        
        # push buttons
        self.start_scan_button = QtWidgets.QPushButton("Start Scan")
        self.stop_scan_button = QtWidgets.QPushButton("Stop Scan")
        self.trigger_opto_button = QtWidgets.QPushButton("Trigger Opto Stim")

        self.load_exp_button = QtWidgets.QPushButton("Load Experiment")
        self.run_exp_button = QtWidgets.QPushButton("Run Experiment")
        self.abort_exp_button = QtWidgets.QPushButton("Abort Experiment")

        self.reset_plots_button = QtWidgets.QPushButton("Reset Plots")

        # checkboxes
        self.launch_fictrac_checkbox = QtWidgets.QCheckBox("Launch Fictrac")
        self.send_orientation_checkbox = QtWidgets.QCheckBox("Send Orientation Data")
        

        
        # plot views
        self.cumm_path_view = pg.widgets.RemoteGraphicsView.RemoteGraphicsView()
        self.cumm_path_view.pg.setConfigOptions(antialias = True)
        self.cumm_path_view.setWindowTitle("Cumulative Path")
        self.app.aboutToQuit.connect(self.cumm_path_view.close)
        self.cumm_path_plotitem = self.cumm_path_view.pg.PlotItem(title="Cumulative Path")
        self.cumm_path_plotitem._setProxyOptions(deferGetattr=True)
        self.cumm_path_view.setCentralItem(self.cumm_path_plotitem)
        

        self.heading_hist_view = pg.widgets.RemoteGraphicsView.RemoteGraphicsView()
        self.heading_hist_view.pg.setConfigOptions(antialias = True)
        self.heading_hist_view.setWindowTitle("Heading Histogram")
        self.app.aboutToQuit.connect(self.heading_hist_view.close)
        self.heading_hist_plotitem = self.heading_hist_view.pg.PlotItem(title="Heading Histogram")
        self.heading_hist_plotitem._setProxyOptions(deferGetattr=True)
        self.heading_hist_plotitem.setXRange(-1*np.pi/16,2*np.pi + np.pi/16)
        self.heading_hist_view.setCentralItem(self.heading_hist_plotitem)

        self.current_heading_view = pg.widgets.RemoteGraphicsView.RemoteGraphicsView()
        self.current_heading_view.pg.setConfigOptions(antialias = True)
        self.current_heading_view.setWindowTitle("Current Heading")
        self.app.aboutToQuit.connect(self.current_heading_view.close)
        self.current_heading_plotitem = self.current_heading_view.pg.PlotItem(title="Current Heading")
        self.current_heading_plotitem._setProxyOptions(deferGetattr=True)
        self.current_heading_plotitem.setAspectLocked(lock=True, ratio=1)
        self.current_heading_plotitem.showAxis('left', False)
        self.current_heading_plotitem.showAxis('bottom', False)
        self.current_heading_plotitem.setXRange(-1,1)
        self.current_heading_plotitem.setYRange(-1,1)
        self.current_heading_view.setCentralItem(self.current_heading_plotitem)
        


        # set layout
        self.layout.addWidget(self.start_scan_button, row=0, col=0)
        self.layout.addWidget(self.stop_scan_button, row=0, col=1)
        self.layout.addWidget(self.trigger_opto_button, row=0, col=2)

        self.layout.addWidget(self.load_exp_button, row=0, col=4, colspan=2)
        self.layout.addWidget(self.run_exp_button, row=1, col=4)
        self.layout.addWidget(self.abort_exp_button, row=1, col=5)

        self.layout.addWidget(self.reset_plots_button, row=2, col=0)

        self.layout.addWidget(self.launch_fictrac_checkbox, row=1, col=0)
        self.layout.addWidget(self.send_orientation_checkbox, row=1, col=1)
        self.layout.addWidget(self.cumm_path_view,row=3,col=0,colspan=2,rowspan=2)
        self.layout.addWidget(self.heading_hist_view,row=3,col=2,colspan=2,rowspan=2)
        self.layout.addWidget(self.current_heading_view, row=3, col=4, colspan = 2, rowspan=2)

        self.layout.resize(1200,500)
        self.layout.show()
        
  
    
    

if __name__ == '__main__':
    ww = WidgetWindow()
    pg.exec()
