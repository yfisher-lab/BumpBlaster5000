import pyqtgraph as pg
import BumpBlaster5000 as bb
import BumpBlaster5000.vr_interface

import sys

if __name__ == "__main__":
    ui = bb.vr_interface.main.BumpBlaster()
    pg.exec()
    # app = QApplication(sys.argv)
    # form = bb.vr_interface.main.FLUI()
    # form.show()
    # r = app.exec_()
    # sys.exit(r)


    # bb.vr_interface.main.main()
