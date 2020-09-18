# default library
import sys
import os
sys.path.append(os.path.join(os.getcwd(),'Ui'))
sys.path.append(os.path.join(os.getcwd(),'Ion'))
# sys.path.append('D:/Documents/208Code/LaserLock/Ui')
# sys.path.append('D:/Documents/208Code/LaserLock/Ion')

from PyQt5.QtWidgets import QVBoxLayout,QGridLayout, QHBoxLayout,QWidget,QLayout,QApplication,QPushButton,QGroupBox
from PyQt5.QtGui import QIcon,QFont
import configparser

# self-built library
from Ui.wlm_web import wlm_web

from Ui.LaserLockCtrl import window
from Ui.TTL import TTLCtrl
from Ui.AD5791 import AD5791Ctrl
from Ui.LoadIonCtrl import LoadIonCtrl
from Ui.PMT import PMTCtrl
# from Ion.load_ion import load_ion

# make the icon normal in the windows taskbar
import ctypes
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("myappid")

# auto-configuration the laser from file
config = configparser.ConfigParser()
config.read('config.ini')

class mainWindow(QWidget):
    def __init__(self, parent=None):
        super(mainWindow, self).__init__(parent)
        wlm = wlm_web()

        # laser control window
        self.laser_num = len(config.sections())
        layout = QGridLayout()
        laser_windows = [None]*self.laser_num
        for i in range(self.laser_num):
            ip = str(config.get(config.sections()[i],'ip'))
            channel = int(config.get(config.sections()[i],'channel'))
            default_fre = float(config.get(config.sections()[i], 'default_fre'))
            laser_windows[i]=window(ip,channel,default_fre,wlm)
            # layout.addWidget(laser_windows[i],i,1,1,4)
        
        # ttl client
        shutter_labels = ['370 Zero', '399', 'Flip Mirror']
        shutter_coms = [0,2,1]
        shutters = [None]*3
        for i in range(3):
            shutters[i] = TTLCtrl(shutter_coms[i],shutter_labels[i])
            # layout.addWidget(shutters[i],i,5,1,1)
        
        """
        g0 = QGroupBox()
        g1 = QGroupBox()
        g2 = QGroupBox()
        g3 = QGroupBox()

        l0 = QHBoxLayout(g0)
        l1 = QHBoxLayout(g1)
        l2 = QHBoxLayout(g2)
        l3 = QHBoxLayout(g3)

        l0.addWidget(laser_windows[0],3)
        l0.addWidget(shutters[0])
        l1.addWidget(laser_windows[1],3)
        l1.addWidget(shutters[1])
        l2.addWidget(laser_windows[2],3)
        l2.addWidget(shutters[2])

        

        l3.addWidget(ad,3)
        l3.addWidget(loadion,1)

        layout.addWidget(g0,0,0,1,5)
        layout.addWidget(g1,1,0,1,5)
        layout.addWidget(g2,2,0,1,5)
        layout.addWidget(g3,3,0,1,5)
        
        """
        ad = AD5791Ctrl()
        loadion = LoadIonCtrl()

        # for convenience add ad and loadion to laser_windows and shutters
        # so that we can add all widgets in one loop
        laser_windows.append(ad)
        shutters.append(loadion)

        """
        gboxs = [QGroupBox(),QGroupBox(),QGroupBox(),QGroupBox()]
        layouts = [QHBoxLayout(item) for item in gboxs]
        for i in range(4):
            layouts[i].addWidget(laser_windows[i],4)
            layouts[i].addWidget(shutters[i],1)
            layout.addWidget(gboxs[i],i,0,1,7)
        """
        g1 = QGroupBox()
        l1 = QGridLayout(g1)
        for i in range(4):
            l1.addWidget(laser_windows[i],i,0,1,4)
            l1.addWidget(shutters[i],i,4,1,1)
        """
        g2 = QGroupBox()
        l2 = QGridLayout(g2)
        l2.addWidget(laser_windows[3],0,0,1,4)
        l2.addWidget(shutters[3],0,4,1,1)
        """

        layout.addWidget(g1,0,0,4,5)
        g1.setFixedHeight(530)
        """
        layout.addWidget(g2,3,0,1,4)
        """
        # AD5791 and LoadIonCtrl
        

        hide_pmt = QPushButton('>')
        hide_pmt.setFont(QFont('Arial',16,24))
        hide_pmt.setCheckable(True)
        hide_pmt.setFixedSize(10,400)
        # hide_pmt.setChecked(True)
        hide_pmt.toggled.connect(self.show_pmt)

        pmt = PMTCtrl()
        pmt.hide()

        """
        g2 = QGroupBox()
        l2 = QGridLayout(g2)
        l2.addWidget(hide_pmt,0,0,4,1)
        l2.addWidget(pmt,0,1,4,5)
        g2.setFixedHeight(450)
        layout.addWidget(g2,0,6,4,5)
        
        """
        layout.addWidget(hide_pmt,0,4,4,1)
        layout.addWidget(pmt,0,5,4,5)
        layout.setSizeConstraint(QLayout.SetFixedSize)
        
        # self.setGeometry(300, 300,900,600)
        self.hide_pmt = hide_pmt
        self.pmt = pmt
        self.setLayout(layout)

        self.setWindowIcon(QIcon('wave.png'))
        self.setWindowTitle('Laser Control')
        # self.setFixedHeight(500)
        # self.setFixedSize(800,400)
        # self.setGeometry(200,300,900,300)
    
    def show_pmt(self):
        if self.hide_pmt.isChecked():
            self.pmt.show()
            self.hide_pmt.setChecked(True)
            self.hide_pmt.setText("<")
        else:
            self.pmt.hide()
            self.hide_pmt.setChecked(False)
            self.hide_pmt.setText(">")
        """
        QApplication.processEvents()
        self.setFixedSize(self.minimumSizeHint())
        """

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    ex = mainWindow()
    ex.show()
    sys.exit(app.exec_())
    