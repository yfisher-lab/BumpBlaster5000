
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets, QtGui

class MainWindow(object):
    def __init__(self):
        self.app = pg.mkQApp("BumpBlaster5000 Interface")
        
        self.layout = pg.LayoutWidget()
        
        # number of slices
        self.num_slices_label = QtWidgets.QLabel()
        self.num_slices_label.setText("Number of Slices:")
        self.num_slices_input = QtWidgets.QLineEdit()
        
        # begin read raw data stream
        self.start_rrds_button = QtWidgets.QPushButton("Begin ReadRawDataStream")
        
        # ch 1 viewing
        
        
        
        
        
        
        self.layout.addWidget(self.num_slices_label)
        self.layout.addWidget(self.num_slices_input)
        
        self.layout.addWidget(self.start_rrds_button)
        
        self.layout.show()
        
        
class RemotePlottingWindow(object):
    
    def __init__(self):
        self.app = pg.mkQApp("Remote Plotting Window")
        
if __name__ == '__main__':
    mw = MainWindow()
    pg.exec()
