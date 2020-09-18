
import sys
import socket

from PyQt5.QtWidgets import QApplication, QWidget, QPushButton,QVBoxLayout,QLabel
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt


# global configuration
myfont = QFont('Arial',12,24)
myfont.setBold(True)

class shutter(object):
    def __init__(self,ip = '192.168.1.16',port=6666,com=2):
        self.com=com
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((ip,port))

    def on(self):
        code = str(self.com) + ' on'
        self.sock.send(code.encode('utf-8'))
        print(self.sock.recv(1024).decode('utf-8'))

    def off(self):
        code = str(self.com) + ' off'
        self.sock.send(code.encode('utf-8'))
        print(self.sock.recv(1024).decode('utf-8'))


class TTLCtrl(QWidget):
    def __init__(self,ttl_com=1, label=' ',parent=None):
        super(TTLCtrl, self).__init__(parent)
        self.shutter = shutter(com = ttl_com)
        self.label = label
        self.initUi()
    
    def initUi(self):
        # define buttons
        l1 = QLabel(self.label)
        l1.setFixedSize(80,33)
        l1.setAlignment(Qt.AlignCenter)
        l1.setFont(myfont)

        btn1 = QPushButton('OFF')
        btn1.setFixedSize(80,33)
        btn1.setCheckable(True)
        btn1.setChecked(False)
        btn1.setStyleSheet('background-color:red')
        btn1.setFont(myfont)
        btn1.toggled.connect(self.change_switch)

        # setup layout
        layout = QVBoxLayout()
        layout.addWidget(l1,0)
        layout.addWidget(btn1,1)

        self.btn1 = btn1
        self.setLayout(layout)

    def change_switch(self):
        if self.btn1.isChecked():
            self.btn1.setChecked(True)
            self.btn1.setStyleSheet('background-color:green')
            self.btn1.setText('ON')
            self.shutter.on()
        else:
            self.btn1.setChecked(False)
            self.btn1.setStyleSheet('background-color:red')
            self.btn1.setText('OFF')   
            self.shutter.off()     

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    l1 = '370 Zero'
    ttl_com = 0
    ex = TTLCtrl(ttl_com,l1)
    ex.show()

    sys.exit(app.exec_())