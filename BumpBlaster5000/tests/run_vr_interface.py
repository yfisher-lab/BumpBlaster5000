import BumpBlaster5000 as bb
import BumpBlaster5000.vr_interface
from PySide2.QtWidgets import QApplication
import sys

if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = bb.vr_interface.main.FLUI()
    form.show()
    r = app.exec_()
    sys.exit(r)


    # bb.vr_interface.main.main()
