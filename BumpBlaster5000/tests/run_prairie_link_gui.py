import pyqtgraph as pg
import BumpBlaster5000 as bb
import BumpBlaster5000.prairie_link_client


if __name__ == "__main__":
    gui = bb.prairie_link_client.pg_gui.MainWindow()
    r_gui = bb.prairie_link_client.pg_gui.RemotePlottingWindow()
    pg.exec()