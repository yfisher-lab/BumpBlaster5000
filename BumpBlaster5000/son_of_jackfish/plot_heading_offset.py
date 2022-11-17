from time import perf_counter

import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets

# import BumpBlaster5000
# from BumpBlaster5000.utils import pol2cart
from utils import pol2cart

# def update():

    # read queue


app = pg.mkQApp() #QtGui.QApplication([])

# win = pg.GraphicsLayoutWidget(show=True, title = "Heading Plots")
win = pg.LayoutWidget()
win.resize(600,600)
# Enable antialiasing for prettier plots
pg.setConfigOptions(antialias=True)

remotes = {i: {'view':pg.widgets.RemoteGraphicsView.RemoteGraphicsView(), 'plt': []} for i in range(1)}
for k, rv in remotes.items():
    rv['view'].pg.setConfigOptions(antialias = True)
    app.aboutToQuit.connect(rv['view'].close)

# remote_view = pg.widgets.RemoteGraphicsView.RemoteGraphicsView()
# remote_view.pg.setConfigOptions(antialias=True)
# app.aboutToQuit.connect(remote_view.close)

label = QtWidgets.QLabel()
layout = pg.LayoutWidget()
layout.addWidget(label)
for i, (k,rv) in enumerate(remotes.items()):
    layout.addWidget(rv['view'],row=i+1, col=0)

# layout.addWidget(remote_view, row=1, col=0)
layout.resize(800,800)
layout.show()


for k, rv in remotes.items():
    rv['plot'] = rv['view'].pg.PlotItem()
    rv['plot']._setProxyOptions(deferGetattr=True)
    rv['plot'].setAspectLocked(lock=True, ratio=1)
    rv['plot'].showAxis('left', False)
    rv['plot'].showAxis('bottom', False)
    rv['plot'].setXRange(-.08, .08)
    rv['plot'].setYRange(-.08, .08)
    # rv['plot'].addItem(pg.EllipseROI([70, 70], [10, 10], pen=(3, 9), 
                # rotatable=False, scaleSnap=True, translateSnap=True))
    rv['view'].setCentralItem(rv['plot'])


# rplt = rplt_widget.getPlotItem() #remote_view.pg.PlotItem()
# rplt._setProxyOptions(deferGetattr=True)
# rplt.setAspectLocked(lock=True, ratio=1)
# rplt.showAxis('left', False)
# rplt.showAxis('bottom', False)
# rplt.setXRange(-.08, .08)
# rplt.setYRange(-.08, .08)
# remote_view.setCentralItem(rplt)




theta = np.pi/2
x,y = .06*np.cos(theta), .06*np.sin(theta)
# curve = p_fly_orientation.plot([0,x], [0,y], pen=(200, 200, 200), symbolBrush=(255, 0, 0), symbolPen='w')
# curve = rplt.plot([0,x], [0,y], pen=(200, 200, 200), symbolBrush=(255, 0, 0), symbolPen='w')
# curve2 = rplt2.plot([0,x], [0,y], pen=(200, 200, 200), symbolBrush=(255, 0, 0), symbolPen='w')
last_update=perf_counter()
avg_fps = 0.
def update():
    # global theta, curve, label, avg_fps, last_update, rpltfunc
    global theta, label, avg_fps, last_update, remotes
    # global theta, curve, label, avg_fps, last_update
    theta = (theta+.01)%(2*np.pi)
    x,y = pol2cart(.06, theta)
    x, y = .06 * np.cos(theta), .06 * np.sin(theta)
    # curve.setData([0,x],[0,y], _callSync='off')
    for k, rv in remotes.items():
        rv['plot'].plot([0,x], [0,y], pen=(200, 200, 200), symbolBrush=(255, 0, 0),
                     symbolPen='w', clear = True, _callSync='off')
    # curve = rplt.plot([0,x], [0,y], pen=(200, 200, 200), symbolBrush=(255, 0, 0),
    #                  symbolPen='w', clear = True, _callSync='off')

    now = perf_counter()
    fps = 1.0/ (now-last_update)
    last_update = now
    avg_fps = avg_fps *0.8 +fps*0.2
    label.setText("Generating %0.2f fps" % avg_fps)


timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(5)


## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    pg.exec()
    # import sys
    # if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
    #     pg.exec()
