
import os, sys
sys.path.append('./')
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QSize, QRect
# from PyQt5.QtWidgets import QDoubleSpinBox, QApplication, QHBoxLayout, QGroupBox, QWidget, QPushButton, QGridLayout, QLabel
import socket
import sys
from ctypes import *

myfont = QFont('Arial',16,24)
myfont.setBold(True)

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

class AD5791:
    """This class is designed to control AD5791, and I have set the LDAC at the Low level which enable Synchronous DAC Update 
 at the rising edge of SYNC."""
    def __init__(self, ser="BSPT002029", dll="usb2uis.dll"):
        self.VREF = 10.0
        self.serial_num = ser
        # dll_path = os.path.join(os.getcwd(),dll)
        # print(dll_path)
        dll_path = os.path.join(os.getcwd(),dll)
        self.dll = cdll.LoadLibrary(dll_path)
        # Close the connections if already exist
        self.dll.USBIO_CloseDeviceByNumber(ser)
        self.device_num = self.dll.USBIO_OpenDeviceByNumber(ser)
        if self.device_num == 0xFF:
            print("No USB2UIS can be connected!")
            exit()
        self.SPI_Init()
        self.device_start()
        
    def SPI_Init(self, frequency=8, mode=1, timeout_read=100, timeout_write=100):
        """SPI settings, frequency upto 8 selections, representing 200kHz 400kHz, 600kHz, 800kHz, 1MHz, 2MHz, 4MHz, 6MHz and 12MHz. Mode is specified to the clock signal, and the timeout is used to specify the timeout of read and write, occupying 16-bit data respectively"""
        self.dll.USBIO_SPISetConfig(self.device_num, (mode<<4)+frequency, (timeout_write<<16)+timeout_read)

    def data(self, Vout):
        return int((Vout+self.VREF)*(2**20-1)/2/self.VREF)
    
    def device_start(self):
        """Set the control register to enable the dac into a normal operation mode and offset code style"""
        self.dll.USBIO_SPIWrite(self.device_num, None, 0, (0x200012).to_bytes(3, byteorder="big"), 3)
    def set_voltage(self, Vout):
        """The Vout set to the DAC should exceed \pm 10V"""
        if abs(Vout)>10.0001:
            print("Voltage over range!")
        else:
            self.dll.USBIO_SPIWrite(self.device_num, None, 0, ((0x01<<20) + self.data(Vout)).to_bytes(3, byteorder="big"), 3)
    def read_voltage(self):
        out = b'\x00'*3
        self.dll.USBIO_SPIWrite(self.device_num, None, 0, (0x900000).to_bytes(3, byteorder="big"), 3)
        self.dll.USBIO_SPIRead(self.device_num, None, 0, out, 3)
        data = int.from_bytes(out, byteorder="big")
        data = data&0x0FFFFF
        return data*2*self.VREF/(2**20 - 1) - self.VREF

    def LDAC(self):
        self.dll.USBIO_SPIWrite(self.device_num, None, 0, (0x400001).to_bytes(3, byteorder="big"), 3)
    def clear(self):
        self.dll.USBIO_SPIWrite(self.device_num, None, 0, (0x400002).to_bytes(3, byteorder="big"), 3)
    def reset(self):
        self.dll.USBIO_SPIWrite(self.device_num, None, 0, (0x400004).to_bytes(3, byteorder="big"), 3)
    def disable_output(self):
        self.dll.USBIO_SPIWrite(self.device_num, None, 0, (0x20001E).to_bytes(3, byteorder="big"), 3)
    def __del__(self):
        self.dll.USBIO_CloseDeviceByNumber(self.serial_num)

class AD5791Ctrl(QGroupBox):
    def __init__(self, ser="BSPT002029", dll="usb2uis.dll"):
        super().__init__()
        self.device = AD5791(ser, dll)
        self.value = LVSpinBox()
        self.value.setFont(myfont)
        self.value.setDecimals(3)
        self.value.setValue(self.device.read_voltage())



        self.switch = QPushButton("ON")
        self.switch.setCheckable(True)
        self.switch.setChecked(True)
        self.switch.setStyleSheet("background-color: green")
        self.switch.setFont(myfont)
        self.reset = QPushButton("Reset")
        self.reset.setFont(myfont)
        self.level = QPushButton("High")
        self.level.setCheckable(True)
        self.level.setChecked(True)
        self.level.setFont(myfont)
        self.level.setStyleSheet("background-color: red")
        layout = QHBoxLayout()
        
        l1 = QLabel("Vref")
        l1.setFont(myfont)
        layout.addWidget(l1, 0)

        layout.addWidget(self.value, 1)
        layout.addWidget(self.level, 1)
        layout.addWidget(self.switch, 1)
        layout.addWidget(self.reset, 1)
        self.setLayout(layout)
        self.set_connect()
        self.level.setChecked(False)
        

    def setRange(self, low=3.5, upper=12.0):
        self.value.setRange(low, upper)

    def set_connect(self):
        self.value.valueChanged.connect(self.set_voltage)
        self.switch.toggled.connect(self.set_switch)
        self.reset.clicked.connect(self.resetAll)
        self.level.toggled.connect(self.changeLevel)
    def set_voltage(self):
        self.device.set_voltage(self.value.value())
    def set_switch(self):
        if self.switch.isChecked():
            self.device.device_start()
            self.level.setChecked(False)
            self.switch.setStyleSheet("background-color: green")
            self.switch.setText("ON")
        else:
            self.device.disable_output()
            self.switch.setStyleSheet("background-color: red")
            self.switch.setText("OFF")
    def resetAll(self):
        self.device.reset()
        self.switch.setChecked(False)
        self.value.setValue(self.device.read_voltage())
    def changeLevel(self):
        if self.level.isChecked():
            self.value.setValue(10.0)
            self.level.setStyleSheet("background-color: green")
            self.level.setText("High")
        else:
            self.value.setValue(3.6)
            self.level.setStyleSheet("background-color: red")
            self.level.setText("Low")
    def setHighLevel(self, state):
        if state:
            self.level.setChecked(True)
        else:
            self.level.setChecked(False)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    ex = AD5791Ctrl()

    ex.show()
    sys.exit(app.exec_())
