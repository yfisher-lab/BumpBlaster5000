# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'guiiZfzlR.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

import pyqtgraph as pg
# from pyqtgraph import PlotWidget


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.setWindowModality(Qt.WindowModal)
        MainWindow.resize(870, 531)
        palette = QPalette()
        brush = QBrush(QColor(222, 221, 218, 255))
        brush.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.WindowText, brush)
        brush1 = QBrush(QColor(5, 77, 72, 255))
        brush1.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.Button, brush1)
        brush2 = QBrush(QColor(54, 46, 73, 255))
        brush2.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.Light, brush2)
        brush3 = QBrush(QColor(45, 38, 61, 255))
        brush3.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.Midlight, brush3)
        brush4 = QBrush(QColor(18, 15, 24, 255))
        brush4.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.Dark, brush4)
        brush5 = QBrush(QColor(24, 21, 33, 255))
        brush5.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.Mid, brush5)
        palette.setBrush(QPalette.Active, QPalette.Text, brush)
        brush6 = QBrush(QColor(191, 191, 191, 255))
        brush6.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.BrightText, brush6)
        brush7 = QBrush(QColor(0, 0, 0, 255))
        brush7.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.ButtonText, brush7)
        palette.setBrush(QPalette.Active, QPalette.Base, brush7)
        brush8 = QBrush(QColor(36, 31, 49, 255))
        brush8.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.Window, brush8)
        palette.setBrush(QPalette.Active, QPalette.Shadow, brush7)
        brush9 = QBrush(QColor(48, 140, 198, 255))
        brush9.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.Highlight, brush9)
        palette.setBrush(QPalette.Active, QPalette.AlternateBase, brush4)
        brush10 = QBrush(QColor(255, 255, 220, 255))
        brush10.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.ToolTipBase, brush10)
        palette.setBrush(QPalette.Active, QPalette.ToolTipText, brush7)
        brush11 = QBrush(QColor(222, 221, 218, 128))
        brush11.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette.setBrush(QPalette.Active, QPalette.PlaceholderText, brush11)
#endif
        palette.setBrush(QPalette.Inactive, QPalette.WindowText, brush)
        palette.setBrush(QPalette.Inactive, QPalette.Button, brush1)
        palette.setBrush(QPalette.Inactive, QPalette.Light, brush2)
        palette.setBrush(QPalette.Inactive, QPalette.Midlight, brush3)
        palette.setBrush(QPalette.Inactive, QPalette.Dark, brush4)
        palette.setBrush(QPalette.Inactive, QPalette.Mid, brush5)
        palette.setBrush(QPalette.Inactive, QPalette.Text, brush)
        palette.setBrush(QPalette.Inactive, QPalette.BrightText, brush6)
        palette.setBrush(QPalette.Inactive, QPalette.ButtonText, brush7)
        palette.setBrush(QPalette.Inactive, QPalette.Base, brush7)
        palette.setBrush(QPalette.Inactive, QPalette.Window, brush8)
        palette.setBrush(QPalette.Inactive, QPalette.Shadow, brush7)
        palette.setBrush(QPalette.Inactive, QPalette.Highlight, brush9)
        palette.setBrush(QPalette.Inactive, QPalette.AlternateBase, brush4)
        palette.setBrush(QPalette.Inactive, QPalette.ToolTipBase, brush10)
        palette.setBrush(QPalette.Inactive, QPalette.ToolTipText, brush7)
        brush12 = QBrush(QColor(222, 221, 218, 128))
        brush12.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette.setBrush(QPalette.Inactive, QPalette.PlaceholderText, brush12)
#endif
        palette.setBrush(QPalette.Disabled, QPalette.WindowText, brush4)
        palette.setBrush(QPalette.Disabled, QPalette.Button, brush1)
        palette.setBrush(QPalette.Disabled, QPalette.Light, brush2)
        palette.setBrush(QPalette.Disabled, QPalette.Midlight, brush3)
        palette.setBrush(QPalette.Disabled, QPalette.Dark, brush4)
        palette.setBrush(QPalette.Disabled, QPalette.Mid, brush5)
        palette.setBrush(QPalette.Disabled, QPalette.Text, brush4)
        palette.setBrush(QPalette.Disabled, QPalette.BrightText, brush6)
        palette.setBrush(QPalette.Disabled, QPalette.ButtonText, brush4)
        palette.setBrush(QPalette.Disabled, QPalette.Base, brush8)
        palette.setBrush(QPalette.Disabled, QPalette.Window, brush8)
        palette.setBrush(QPalette.Disabled, QPalette.Shadow, brush7)
        brush13 = QBrush(QColor(145, 145, 145, 255))
        brush13.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Disabled, QPalette.Highlight, brush13)
        palette.setBrush(QPalette.Disabled, QPalette.AlternateBase, brush8)
        palette.setBrush(QPalette.Disabled, QPalette.ToolTipBase, brush10)
        palette.setBrush(QPalette.Disabled, QPalette.ToolTipText, brush7)
        brush14 = QBrush(QColor(222, 221, 218, 128))
        brush14.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette.setBrush(QPalette.Disabled, QPalette.PlaceholderText, brush14)
#endif
        MainWindow.setPalette(palette)
        MainWindow.setUnifiedTitleAndToolBarOnMac(True)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.start_scan_push = QPushButton(self.centralwidget)
        self.start_scan_push.setObjectName(u"start_scan_push")
        self.start_scan_push.setEnabled(True)
        self.start_scan_push.setGeometry(QRect(30, 40, 121, 31))
        font = QFont()
        font.setFamily(u"Arial")
        font.setPointSize(13)
        self.start_scan_push.setFont(font)
        self.trigger_opto_push = QPushButton(self.centralwidget)
        self.trigger_opto_push.setObjectName(u"trigger_opto_push")
        self.trigger_opto_push.setEnabled(True)
        self.trigger_opto_push.setGeometry(QRect(290, 40, 151, 31))
        self.trigger_opto_push.setFont(font)
        self.heading_occ_plotwidget = PlotWidget(self.centralwidget)
        self.heading_occ_plotwidget.setObjectName(u"heading_occ_plotwidget")
        self.heading_occ_plotwidget.setGeometry(QRect(510, 200, 321, 231))
        self.exp_filepath_push = QPushButton(self.centralwidget)
        self.exp_filepath_push.setObjectName(u"exp_filepath_push")
        self.exp_filepath_push.setGeometry(QRect(490, 20, 341, 70))
        self.exp_filepath_label = QLabel(self.centralwidget)
        self.exp_filepath_label.setObjectName(u"exp_filepath_label")
        self.exp_filepath_label.setGeometry(QRect(490, 90, 341, 30))
        font1 = QFont()
        font1.setFamily(u"Sans Serif")
        font1.setPointSize(12)
        self.exp_filepath_label.setFont(font1)
        self.exp_filepath_label.setAlignment(Qt.AlignCenter)
        self.heading_occ_label = QLabel(self.centralwidget)
        self.heading_occ_label.setObjectName(u"heading_occ_label")
        self.heading_occ_label.setGeometry(QRect(510, 430, 231, 20))
        self.heading_occ_label.setFont(font)
        self.stop_scan_push = QPushButton(self.centralwidget)
        self.stop_scan_push.setObjectName(u"stop_scan_push")
        self.stop_scan_push.setEnabled(True)
        self.stop_scan_push.setGeometry(QRect(170, 40, 101, 31))
        self.stop_scan_push.setFont(font)
        self.launch_fictrac_toggle = QCheckBox(self.centralwidget)
        self.launch_fictrac_toggle.setObjectName(u"launch_fictrac_toggle")
        self.launch_fictrac_toggle.setGeometry(QRect(40, 120, 121, 23))
        self.launch_fictrac_toggle.setChecked(False)
        self.save_fictrac_toggle = QCheckBox(self.centralwidget)
        self.save_fictrac_toggle.setObjectName(u"save_fictrac_toggle")
        self.save_fictrac_toggle.setGeometry(QRect(170, 120, 121, 23))
        self.save_fictrac_toggle.setChecked(False)
        self.cumm_path_label = QLabel(self.centralwidget)
        self.cumm_path_label.setObjectName(u"cumm_path_label")
        self.cumm_path_label.setGeometry(QRect(30, 430, 140, 20))
        self.cumm_path_label.setFont(font)
        self.send_orientation_toggle = QCheckBox(self.centralwidget)
        self.send_orientation_toggle.setObjectName(u"send_orientation_toggle")
        self.send_orientation_toggle.setGeometry(QRect(40, 150, 165, 37))
        self.run_exp_push = QPushButton(self.centralwidget)
        self.run_exp_push.setObjectName(u"run_exp_push")
        self.run_exp_push.setGeometry(QRect(490, 130, 161, 41))
        self.abort_exp_push = QPushButton(self.centralwidget)
        self.abort_exp_push.setObjectName(u"abort_exp_push")
        self.abort_exp_push.setGeometry(QRect(670, 130, 161, 41))
        self.cumm_path_plotwidget = PlotWidget(self.centralwidget)
        self.cumm_path_plotwidget.setObjectName(u"cumm_path_plotwidget")
        self.cumm_path_plotwidget.setGeometry(QRect(30, 200, 321, 231))
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusBar = QStatusBar(MainWindow)
        self.statusBar.setObjectName(u"statusBar")
        MainWindow.setStatusBar(self.statusBar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.start_scan_push.setText(QCoreApplication.translate("MainWindow", u"Start Scan", None))
        self.trigger_opto_push.setText(QCoreApplication.translate("MainWindow", u"Trigger Opto Stim", None))
        self.exp_filepath_push.setText(QCoreApplication.translate("MainWindow", u"Load Experiment", None))
        self.exp_filepath_label.setText(QCoreApplication.translate("MainWindow", u"No File Selected", None))
        self.heading_occ_label.setText(QCoreApplication.translate("MainWindow", u"Heading Occupancy History", None))
        self.stop_scan_push.setText(QCoreApplication.translate("MainWindow", u"Stop Scan ", None))
        self.launch_fictrac_toggle.setText(QCoreApplication.translate("MainWindow", u"Launch Fictrac", None))
        self.save_fictrac_toggle.setText(QCoreApplication.translate("MainWindow", u"Save Fictrac", None))
        self.cumm_path_label.setText(QCoreApplication.translate("MainWindow", u"Cumulative Path", None))
        self.send_orientation_toggle.setText(QCoreApplication.translate("MainWindow", u"Send Orientation Data", None))
        self.run_exp_push.setText(QCoreApplication.translate("MainWindow", u"Run Experiment", None))
        self.abort_exp_push.setText(QCoreApplication.translate("MainWindow", u"Abort Experiment", None))
    # retranslateUi

