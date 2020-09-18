
import sys

import time
from toptica_laser import toptica_laser as laser

from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QGridLayout, QDoubleSpinBox, QLCDNumber, QMessageBox, QLabel
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QThread

from wlm_web import wlm_web

myfont = QtGui.QFont('Arial', 16, 24)
myfont.setBold(True)

# TODO:fix the error of wlm, sometimes when the channel is ticked off, there is still wavelength not -3


class laserLockWorker(QThread):

    def __init__(self, ob):
        super(laserLockWorker, self).__init__()
        self.ob = ob
        self.isWork = False

    def run(self):
        
        while True:
            temp = self.ob._data[self.ob.channel]
            if self.isWork:
                if self.ob.laser.get_status() and (temp != -3. or -4.):
                    self.ob.laser.lock(temp, self.ob.spin1.value())
                    if abs(temp-self.ob.spin1.value()) > 0.000003:
                        self.ob.btn1.setStyleSheet('background-color:yellow')
                        self.ob.btn1.setText('Locking...')
                    else:
                        self.ob.btn1.setStyleSheet('background-color:green')
                        self.ob.btn1.setText('Locked')
                else:
                    QMessageBox.warning(self.ob, 'Warning',
                                        'Laser or WavelenghtMeter is OFF')
                    break
            time.sleep(0.5)
    def startWork(self,iswork=True):
        self.isWork = iswork


class refreshData(QThread):
    sinOut = pyqtSignal()

    def __init__(self, ob):
        super(refreshData, self).__init__()
        self.ob = ob
        self.isWork = True

    def run(self):
        # global refreshedData
        while self.isWork:
            # refreshedData =
            self.ob._data = self.ob.wlm.get_data()
            self.ob.lcd1.display('%.6f' % self.ob._data[self.ob.channel])
            # print(refreshedData)
            # self.sinOut.emit()
            time.sleep(0.05)

    def stop(self):
        self.isWork = False

class refreshVoltage(QThread):
    def __init__(self,ob):
        super(refreshVoltage, self).__init__()
        self.ob = ob
        self.isWork = True

    def run(self):
        while True:
            if self.isWork:
                self.ob.laser.set_voltage(self.ob.vol_spin.value())                
            time.sleep(0.02)

    def setWork(self,iswork=False):
        self.isWork = iswork

class refreshVoltage2(QThread):
    def __init__(self,ob):
        super(refreshVoltage2, self).__init__()
        self.ob = ob
        self.isWork = True

    def run(self):
        while True:
            if self.isWork:
                laser_vol = self.ob.laser.get_voltage()
                self.ob.vol_spin.setValue(laser_vol)
                # print('thread read vol:%s' % laser_vol)
            time.sleep(0.02)
            # print("working:%s" % self.isWork)

    def setWork(self,iswork=False):
        self.isWork = iswork

class LVSpinBox(QDoubleSpinBox):
    '''This class is a reimplemented double spinbox with the same function as LabView number control'''
    stepChanged = pyqtSignal()

    def stepBy(self, step):
        value = self.value()
        point = str(self.text()).find('.')
        if point < 0:
            point = len(str(self.text()))
        digit = point - self.lineEdit().cursorPosition()
        if digit < 0:
            digit += 1
        self.setValue(value + step*(10**digit))
        if self.value() != value:
            self.stepChanged.emit()

    def onValueChanged(self, func):
        self.editingFinished.connect(func)
        self.stepChanged.connect(func)


class window(QWidget):
    def __init__(self, laser_ip, laser_channel, default_fre, wlm, parent=None):
        super(window, self).__init__(parent)
        print(laser_ip)
        self.wlm = wlm
        self.setWindowTitle('Laser Panel')
        self.setWindowIcon(QtGui.QIcon('wave.png'))
        self.default_fre = default_fre
        self.laser = laser(laser_ip)
        self.channel = laser_channel
        self._data = [None]*8

        self.initUi()
        self.show()
        self.t1 = refreshData(self)
        self.t1.start()

        self.t2 = laserLockWorker(self)
        self.t2.start()

        """
        self.t3 = refreshVoltage(self)
        self.t3.start()
        """

        self.refreshVoltage = refreshVoltage2(self)
        self.refreshVoltage.start()
        # self.t1.start()

    def initUi(self):

        # define LCD to show wavelength
        lcd1 = QLCDNumber()
        lcd1.setDigitCount(10)
        lcd1.setSegmentStyle(QLCDNumber.Flat)
        lcd1.display(self.default_fre)
        lcd1.setFont(myfont)
        lcd1.setFixedWidth(300)
        self.lcd1 = lcd1

        # define on/off buttons to control Lock or not
        btn1 = QPushButton('OFF')
        btn1.setCheckable(True)
        btn1.setChecked(False)
        # btn1.toggled.connect(self.print_info)
        btn1.setStyleSheet('background-color:red')
        btn1.setFont(myfont)
        self.btn1 = btn1
        self.btn1.clicked.connect(self.change_switch)

        # define spibox for changing destination lock point
        spin1 = LVSpinBox()
        spin1.setDecimals(6)
        spin1.setRange(0, 1000)
        spin1.setValue(self.default_fre)
        spin1.setFont(myfont)
        self.spin1 = spin1

        # voltage
        vol_spin = LVSpinBox()
        vol_spin.setDecimals(6)
        vol_spin.setRange(-100,200)
        vol_spin.setValue(self.laser.get_voltage())
        vol_spin.setFont(myfont)
        vol_spin.setFixedWidth(125)

        vol_label = QLabel('Voltage')
        vol_label.setFont(myfont)
        vol_label.setAlignment(QtCore.Qt.AlignCenter)
        vol_label.setFixedWidth(125)

        self.vol_spin = vol_spin

        self.vol_spin.valueChanged.connect(self.refreshValue)

        # set up layout
        layout = QGridLayout()
        layout.addWidget(self.lcd1, 0, 0, 2, 4)
        layout.addWidget(self.spin1, 0, 4, 1, 1,)
        layout.addWidget(self.btn1, 1, 4, 1, 1)
        layout.addWidget(vol_label,0,5,1,1)
        layout.addWidget(self.vol_spin,1,5,1,1)

        # self.setGeometry(300, 300, 750, 100)
        self.setLayout(layout)

    def change_switch(self):
        if self.laser.get_status():
            if self.btn1.isChecked():
                self.default_fre = self.spin1.value()
                self.btn1.setChecked(True)
                self.btn1.setStyleSheet('background-color:green')
                self.btn1.setText('ON')
                self.t2.startWork(True)
            else:
                self.btn1.setChecked(False)
                self.btn1.setStyleSheet('background-color:red')
                self.btn1.setText('OFF')
                self.t2.startWork(False)
        else:
            QMessageBox.warning(self, 'Warning', 'Laser is OFF!!!')
            self.t2.startWork(False)
            self.btn1.setChecked(False)
            self.btn1.setStyleSheet('background-color:red')
            self.btn1.setText('OFF')

    def refreshValue(self):
        self.refreshVoltage.setWork(False)
        # time.sleep(0.05)
        # print('vol_spin:%s' % self.vol_spin.value())
        self.laser.set_voltage(self.vol_spin.value())
        # time.sleep(0.01)
        self.refreshVoltage.setWork(True)
"""
    def laser_lock(self):
        temp = self._data[self.channel]
        if self.btn1.isChecked() and self.laser.get_status():
            if (temp != -3. or -4.):
                self.laser.lock(temp, self.spin1.value())
                if abs(temp-self.spin1.value()) > 0.000003:
                    self.btn1.setStyleSheet('background-color:yellow')
                    self.btn1.setText('Locking...')
                else:
                    self.btn1.setStyleSheet('background-color:green')
                    self.btn1.setText('Locked')
            else:
                QMessageBox.warning(
                    self, 'Warning', 'Laser or WavelenghtMeter is OFF')

    # acquire laser frequency and refresh LCDNumber
    def refresh(self):
        self._data = refreshedData
        self.lcd1.display('%.6f' % self._data[self.channel])

    def mytimer(self, func, interval):
        timer = QtCore.QTimer(self)
        timer.timeout.connect(func)
        timer.start(interval)
"""

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    laser_ip = '192.168.1.61'
    laser_channel = 1
    laser_fre = 369.526100
    wlm = wlm_web()
    ex = window(laser_ip, laser_channel, laser_fre, wlm)

    sys.exit(app.exec_())
