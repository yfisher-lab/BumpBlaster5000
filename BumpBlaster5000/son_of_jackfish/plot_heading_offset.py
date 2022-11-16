from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg

import BumpBlaster5000
from BumpBlaster5000.utils import pol2cart




# def update():

    # read queue


app = pg.mkQApp() #QtGui.QApplication([])

win = pg.GraphicsLayoutWidget(show=True, title = "Heading Plots")
win.resize(600,600)


# Enable antialiasing for prettier plots
pg.setConfigOptions(antialias=True)
#
p_fly_orientation = win.addPlot(title="Fly's Heading")
p_fly_orientation.showAxis('left', False)
p_fly_orientation.showAxis('bottom', False)
p_fly_orientation.setAspectLocked(lock=True, ratio=1)
# p_fly_orientation.addLine(x=0, pen=.2)
# p_fly_orientation.addLine(y=0, pen=.2)
p_fly_orientation.setXRange(-.08,.08)
p_fly_orientation.setYRange(-.08,.08)
p_fly_orientation.showGrid(x=True, y=True, alpha = 1)
# for r in np.arange(.001, .08, .01):
#     circle = pg.QtGui.QGraphicsEllipseItem(-r, -r, r * 2, r * 2)
#     circle.setPen(pg.mkPen(0.2))
#     p_fly_orientation.addItem(circle)

theta = np.pi/2
x,y = .06*np.cos(theta), .06*np.sin(theta)
curve = p_fly_orientation.plot([0,x], [0,y], pen=(200, 200, 200), symbolBrush=(255, 0, 0), symbolPen='w')
def update():
    global theta, curve
    theta = (theta+.01)%(2*np.pi)
    x,y = pol2cart(.06, theta)
    # x, y = .06 * np.cos(theta), .06 * np.sin(theta)
    curve.setData([0,x],[0,y])
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start()


## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        pg.exec()
