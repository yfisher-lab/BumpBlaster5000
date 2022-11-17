import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets
import numpy as np


import BumpBlaster5000
from BumpBlaster5000.utils import pol2cart

from time import perf_counter




# def update():

    # read queue


app = pg.mkQApp() #QtGui.QApplication([])

# win = pg.GraphicsLayoutWidget(show=True, title = "Heading Plots")
win = pg.LayoutWidget()
win.resize(600,600)
# Enable antialiasing for prettier plots
pg.setConfigOptions(antialias=True)

# remote_view = pg.widgets.RemoteGraphicsView.RemoteGraphicsView()
# remote_view.pg.setConfigOptions(antialias=True)
# app.aboutToQuit.connect(remote_view.close)

label = QtWidgets.QLabel()
# layout = pg.LayoutWidget()
# layout.addWidget(label)
# layout.addWidget(remote_view, row=1)
# layout.resize(800,800)
# layout.show()

# rplt = remote_view.pg.PlotItem()
# rplt._setProxyOptions(deferGetattr=True)
# rplt.setAspectLocked(lock=True, ratio=1)
# rplt.showAxis('left', False)
# rplt.showAxis('bottom', False)
# rplt.setXRange(-.08, .08)
# rplt.setYRange(-.08, .08)

# remote_view.setCentralItem(rplt)



# #
win.addWidget(label)
p_fly_orientation = pg.PlotWidget(title="Fly's Heading")

p_fly_orientation.showAxis('left', False)
p_fly_orientation.showAxis('bottom', False)
p_fly_orientation.setAspectLocked(lock=True, ratio=1)
p_fly_orientation.addLine(x=0, pen=.2)
p_fly_orientation.addLine(y=0, pen=.2)
p_fly_orientation.setXRange(-.08,.08)
p_fly_orientation.setYRange(-.08,.08)
win.addWidget(p_fly_orientation)
win.show()
# p_fly_orientation.showGrid(x=True, y=True, alpha = 1)
# for r in np.arange(.001, .08, .01):
#     circle = pg.QtGui.QGraphicsEllipseItem(-r, -r, r * 2, r * 2)
#     circle.setPen(pg.mkPen(0.2))
#     p_fly_orientation.addItem(circle)

theta = np.pi/2
x,y = .06*np.cos(theta), .06*np.sin(theta)
curve = p_fly_orientation.plot([0,x], [0,y], pen=(200, 200, 200), symbolBrush=(255, 0, 0), symbolPen='w')
# curve = rplt.plot([0,x], [0,y], pen=(200, 200, 200), symbolBrush=(255, 0, 0), symbolPen='w')
last_update=perf_counter()
avg_fps = 0.
def update():
    # global theta, curve, label, avg_fps, last_update
    global theta, curve, label, avg_fps, last_update
    theta = (theta+.01)%(2*np.pi)
    x,y = pol2cart(.06, theta)
    x, y = .06 * np.cos(theta), .06 * np.sin(theta)
    curve.setData([0,x],[0,y])
    # curve = rplt.plot([0,x], [0,y], pen=(200, 200, 200), symbolBrush=(255, 0, 0),
                    #  symbolPen='w', clear = True)

    now = perf_counter()
    fps = 1.0/ (now-last_update)
    last_update = now
    avg_fps = avg_fps *0.8 +fps*0.2
    label.setText("Generating %0.2f fps" % avg_fps)


timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(0)


## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    pg.exec()
    # import sys
    # if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
    #     pg.exec()
