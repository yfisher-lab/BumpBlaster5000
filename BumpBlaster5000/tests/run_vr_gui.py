import pyqtgraph as pg
import BumpBlaster5000 as bb
import BumpBlaster5000.vr_interface



if __name__ == "__main__":
    gui = bb.vr_interface.pg_gui.WidgetWindow()
    pg.exec()