import pyqtgraph as pg
import BumpBlaster5000 as bb
import BumpBlaster5000.vr_interface



if __name__ == "__main__":
    ui = bb.vr_interface.main.BumpBlaster()
    pg.exec()