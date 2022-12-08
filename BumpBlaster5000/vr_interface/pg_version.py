import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets


class WidgetWindow:
    
    def setup(self):
        self.app = pg.mkQApp("BumpBlaster5000 Interface")
        
        
        self.layout = pg.LayoutWidget()
        
        # push buttons
        self.start_scan_button = QtWidgets.QPushButton("Start Scan")
        self.stop_scan_button = QtWidgets.QPushButton("Stop Scan")
        self.trigger_opto_button = QtWidgets.QPushButton("Trigger Opto Stim")

        self.load_exp_button = QtWidgets.QPushButton("Load Experiment")
        self.run_exp_button = QtWidgets.QPushButton("Run Experiment")
        self.abort_exp_button = QtWidgets.QPushButton("Abort Experiment")

        # checkboxes
        self.launch_fictrac_checkbox = QtWidgets.QCheckBox("Launch Fictrac")
        self.send_orientation_checkbox = QtWidgets.QCheckBox("Send Orientation Data")

        

        self.cumm_path_view = pg.widgets.RemoteGraphicsView.RemoteGraphicsView()
        self.cumm_path_view.pg.setConfigOptions(antialias = True)
        self.cumm_path_view.setWindowTitle("Cumulative Path")
        self.app.aboutToQuit.connect(self.cumm_path_view.close)

        self.heading_hist_view = pg.widgets.RemoteGraphicsView.RemoteGraphicsView()
        self.heading_hist_view.pg.setConfigOptions(antialias = True)
        self.heading_hist_view.setWindowTitle("Heading Histogram")
        self.app.aboutToQuit.connect(self.heading_hist_view.close)



        self.layout.addWidget(self.start_scan_button, row=0, col=0)
        self.layout.addWidget(self.stop_scan_button, row=0, col=1)
        self.layout.addWidget(self.trigger_opto_button, row=0, col=2)

        self.layout.addWidget(self.load_exp_button, row=0, col=4, colspan=3)
        self.layout.addWidget(self.run_exp_button, row=1, col=4)
        self.layout.addWidget(self.abort_exp_button, row=1, col=6)

        self.layout.addWidget(self.launch_fictrac_checkbox, row=1, col=0)
        self.layout.addWidget(self.send_orientation_checkbox, row=1, col=1)
        self.layout.addWidget(self.cumm_path_view,row=2,col=0,colspan=3,rowspan=4)
        self.layout.addWidget(self.heading_hist_view,row=2,col=4,colspan=3,rowspan=4)

        self.layout.resize(800,300)
        self.layout.show()
        
    def set_colors(self):
        pass
    
    

if __name__ == '__main__':
    pg.exec()
