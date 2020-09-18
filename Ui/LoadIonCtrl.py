
import sys
import time
#sys.path.append('D:/Documents/208Code/LaserLock/Ion')
sys.path.append('../Ion/')
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import QApplication,QWidget,QPushButton, QVBoxLayout,QLabel
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from load_ion import IonLoader
import atexit

myfont = QtGui.QFont('Arial',16,24)
myfont.setBold(True)
ion = IonLoader()

class LoadIonWorker(QThread):
    sinOut = pyqtSignal(bool)

    def __init__(self):
        super(LoadIonWorker, self).__init__()

    def __del__(self):
        pass

    def run(self):
        global LoadIonWorkerSignal
        ion.setLoad(True)
        LoadIonWorkerSignal = ion.load_ion()
        self.sinOut.emit(LoadIonWorkerSignal)

    def stop(self):
        ion.setLoad(False)

class CheckIon(QThread):
    sinOut = pyqtSignal(bool)
    def __init__(self):
        super(CheckIon, self).__init__()
        self.HasIon = True
    
    def __del__(self):
        pass

    def run(self):
        while self.HasIon:
            self.HasIon = ion.is_ion()
            time.sleep(2)
        self.sinOut.emit(False)

class LoadIonCtrl(QWidget):

    def __init__(self, parent = None):
        super(LoadIonCtrl, self).__init__(parent)
        self.initUi()
        self.loadIon = LoadIonWorker()
        self.checkIon = CheckIon()
        self.hasIon = False
        atexit.register(self.closeAll)
    def initUi(self):

        # define label and button
        l1 = QLabel('Load Ion')
        l1.setAlignment(QtCore.Qt.AlignCenter)
        l1.setFont(myfont)

        btn1 = QPushButton('OFF')
        btn1.setCheckable(True)
        btn1.setChecked(False)
        btn1.setStyleSheet('background-color:red')
        btn1.setFont(myfont)
        btn1.clicked.connect(self.change_switch)

        # setup layout
        layout = QVBoxLayout()
        layout.addWidget(l1,0)
        layout.addWidget(btn1,1)

        self.btn1 = btn1
        self.setLayout(layout)

    def change_switch(self):

        # 在没有ion的时候检测 load 按钮是否按下，之后执行对应的操作
        if not self.hasIon:
            if self.btn1.isChecked():
                self.btn1.setChecked(True)
                self.btn1.setStyleSheet('background-color:yellow')
                self.btn1.setText('Loading')
                self.loadIon.start()
                self.loadIon.sinOut.connect(self.updateIon2)
            else:
                self.btn1.setChecked(False)
                self.btn1.setStyleSheet('background-color:red')
                self.btn1.setText('Load OFF')
                try:
                    self.loadIon.stop()
                except:
                    pass

        # 在有Ion的显示目前是有离子，并且不断检测
        # 一旦没有离子了，重新设置按钮的状态，并退出检测

        else:
            self.btn1.setChecked(False)
            self.btn1.setStyleSheet('background-color:green')
            self.btn1.setText('Loaded')
            self.checkIon.satrt()
            self.ckeckIon.sinOut.connect(self.updateIon)

    def updateIon(self):
        self.checkIon.stop()
        self.hasIon = False
        self.btn1.setChecked(False)
        self.btn1.setStyleSheet('background-color:red')
        self.btn1.setText('Load OFF')  
    
    def updateIon2(self):
        if LoadIonWorkerSignal:
            self.btn1.setStyleSheet('background-color:green')
            self.btn1.setText('Loaded')
        else:
            self.btn1.setStyleSheet('background-color:red')
            self.btn1.setChecked(False)
            self.btn1.setText('Load OFF')

    
    def closeAll(self):
        ion.setLoad(False)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    ex = LoadIonCtrl()
    ex.show()

    sys.exit(app.exec_())