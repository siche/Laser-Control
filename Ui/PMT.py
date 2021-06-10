
from PyQt5.QtGui import QFont, QIcon
import ctypes
from ttl_client import shutter
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QGridLayout, QLabel, QComboBox, QMessageBox, QLayout
from serial import Serial
import serial.tools.list_ports
import numpy as np
import sys
import time
import pyqtgraph as pg
pg.setConfigOption('background', 'w')


# make the icon normal in the windows taskbar
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("myappid")


myfont = QFont('Arial', 16, 24)
myfont.setBold(True)

data_len = 100

# 当数据更新之后会发送一个signal


class PMTWorker(QThread):
    sinOut = pyqtSignal(list)

    def __init__(self, ser):
        super(PMTWorker, self).__init__()
        if ser:
            ser.baudrate = 115200
            if ser.is_open:
                ser.write(b'e')
                ser.close()

            ser.open()
            ser.write(b's')
            ser.reset_input_buffer()
            ser.reset_output_buffer()
            self._ser = ser
            self.working = True
        else:
            self.working = False
            print('Com Port is not selected')

    # delete something when thread ends

    def __del__(self):
        self._ser.close()
        self.working = False

    def run(self):
        # define data
        # 0:count 1:mean 2:stdv 3:up 4:down
        global data
        data = [[0]*100]*5
        while self.working:
            # average over 15 data
            count = 0
            for k in range(16):
                pmt_data = self._ser.read(2)
                num = int.from_bytes(pmt_data, byteorder='little')
                count += num

            temp_mean = np.mean(data[0])
            temp_stdv = np.std(data[0])

            # update data
            y_now = count/16
            data[0] = data[0][1:] + [y_now]
            data[1] = data[1][1:] + [temp_mean]
            data[2] = data[2][1:] + [temp_stdv]
            data[3] = data[3][1:] + [temp_mean+5*temp_stdv]
            data[4] = data[4][1:] + [temp_mean-5*temp_stdv]

            # emit signal
            self.sinOut.emit(data)


class PMTCtrl(QWidget):
    def __init__(self, parent=None):
        super(PMTCtrl, self).__init__(parent)

        self.initUi()
        self._com = None
        self.setWindowIcon(QIcon('light.png'))
        self.setWindowTitle('PMT')
        # self.shutter = shutter(com=1)

        """ move to the connect signal
        self.thread = PMTWorker(self._com)
        self.thread.sinOut.connect(self.update_plot)
        # self.thread.sinOut.connect(self.mouseMoved)
        self.thread.start()
        """

    def initUi(self):

        # plot figure window
        PltWindow = pg.PlotWidget()
        PltWindow.showGrid(x=True, y=True)
        # PltWindow.setClipToView(True)
        PltWindow.setFont(myfont)

        self.PltText = pg.TextItem()
        self.PltText2 = pg.TextItem()

        PltWindow.addItem(self.PltText)
        PltWindow.addItem(self.PltText2)

        layout = QGridLayout()
        layout.addWidget(PltWindow, 1, 0, 3, 4)

        # self.fig = PltWindow.addPlot()
        # self.fig.setDownsampling(mode='peak')
        # self.fig.setClipToView(True)

        self.fig = PltWindow
        self.curve = self.fig.plot([0]*100)
        self.fig.getAxis('bottom').tickFont = myfont
        self.fig.getAxis('left').tickFont = myfont

        # connection and status button
        btn1 = QComboBox()
        btn1.addItems(['com16'])
        ports = [item[0] for item in list(serial.tools.list_ports.comports())]
        btn1.addItems(ports)
        btn1.setFont(QFont('Arial', 12, 24))

        # connection button
        btn2 = QPushButton('Connect')
        btn2.setCheckable(True)
        btn2.setChecked(False)
        btn2.setStyleSheet('background-color:red')
        btn2.toggled.connect(self.change_switch)

        btn2.setFont(QFont('Arial', 12, 24))

        btn3 = QPushButton('CCD')
        btn3.setStyleSheet('background-color:blue')
        btn3.clicked.connect(lambda: self.on_off(0))
        btn3.setFont(QFont('Arial', 12, 24))


        btn4 = QPushButton('PMT')
        btn4.setStyleSheet('background-color:green')
        btn4.clicked.connect(lambda: self.on_off(1))
        btn4.setFont(QFont('Arial', 12, 24))

        layout.addWidget(btn1, 0, 0, 1, 1)
        layout.addWidget(btn2, 0, 1, 1, 1)
        layout.addWidget(btn3, 0, 2, 1, 1)
        layout.addWidget(btn4, 0, 3, 1, 1)
        layout.setSizeConstraint(QLayout.SetFixedSize)

        # self.setFixedSize(200,256)
        self.comPicker = btn1
        self.connect = btn2

        self.setLayout(layout)
        # self.setFixedHeight(450)
        # self.move_slot = pg.SignalProxy(self.fig.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)

    def on_off(self, num = 3):
        if num==0:
            self.shutter.on()
        if num==1:
            self.shutter.off()

    def change_switch(self):

        if self.connect.isChecked():
            # if the comport already selected
            if self._com == self.comPicker.currentText():
                # QMessageBox.warning(self,'Warning','ComPort Already Selected')
                self.connect.setChecked(True)
                self.connect.setStyleSheet('background-color:green')
                self.connect.setText('Connected')
            else:
                self._com = self.comPicker.currentText()

                # check if the port is in use
                try:
                    ser = Serial(self._com)
                    self.ser = ser
                    self.thread = PMTWorker(self.ser)
                    self.thread.sinOut.connect(self.update_plot)
                    # self.thread.sinOut.connect(self.mouseMoved)
                    self.thread.start()
                    self.connect.setChecked(True)
                    self.connect.setStyleSheet('background-color:green')
                    self.connect.setText('Connected')
                # warning if the port is in use
                except:
                    QMessageBox.warning(
                        self, 'Warning', 'Permission Denied:Selected ComPort is in Use')

        else:
            self.connect.setChecked(False)
            self.connect.setStyleSheet('background-color:red')
            self.connect.setText('UnConnected')
            try:
                self.thread.stop()
                self.ser.close()
            except:
                pass

    def update_plot(self, data):
        if self.connect.isChecked():
            self.curve.setData(data[0][1:], pen=pg.mkPen(width=2.5, color='r'))
            self.PltText.setHtml(
                "<p style='font-size: 10pt; font-family:Arial; color: black'><strong> Count = %0.2f</strong></p>" % data[0][-1])
            self.PltText.setPos(85, 0.9*max(data[0]))
    """
    def timer(self, func, interval):
        timer = QtCore.QTimer(self)
        timer.timer.connect(func)
        timer.start(interval)
    """

    """
    def mouseMoved(self,evt):  # 显示鼠标处坐标
        mousePoint = self.fig.plotItem.vb.mapSceneToView(evt[0])
        if self.connect.isChecked():
            if (mousePoint.x() < 100 and mousePoint.x()>0) and (mousePoint.y() < max(data[0]) and mousePoint.y()>0):
                self.PltText2.setHtml(
                    "<p><font size='3' color='black' face='Arial'> x = %0.2f</font></p> <p><font size='3' color='black' face='Arial'> y = %0.2f</font></p>" % (
                    int(mousePoint.x()), data[0][int(np.floor(mousePoint.y()))]))
                self.PltText2.setPos(mousePoint.x()-5,mousePoint.y())
    """


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    ex = PMTCtrl()
    ex.show()

    sys.exit(app.exec_())
