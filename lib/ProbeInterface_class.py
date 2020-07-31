# -*- coding: utf-8 -*-
#bash! /bin/env/python

##############################################################################################################
# IMPORTATION
##############################################################################################################

import sys, os
sys.path.append('./')

import pyqtgraph as pg

import PyQt5
from PyQt5.QtWidgets    import QMainWindow, QWidget, QApplication, QPushButton, QLabel, QSpinBox, QLineEdit, QDialog
from PyQt5.QtWidgets    import QVBoxLayout, QGridLayout   # main layouts
from PyQt5.QtCore       import pyqtSignal
from PyQt5.QtGui        import QCloseEvent


##############################################################################################################
# FUNCTION
##############################################################################################################



class MainWindow(QMainWindow):
    '''
    Main window of the application that embeds the ThermometerMonitoring widget.
    '''
    def __init__(self):
        super().__init__()
        # ---  --- #
        self.my_dialog = ProbeInterface()
        self.my_dialog.probe_info_sgnl.connect(lambda a,b,c: print(a,b,c))
        # ---  --- #
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        # ---
        layout = QVBoxLayout()
        self.button = QPushButton('test dialog')
        # ---
        layout.addWidget(self.button)
        self.main_widget.setLayout(layout)
        # ---  --- #
        self.button.clicked.connect(self.open_dialog)
        # ---  --- #
        self.show()

    def open_dialog(self):
        value = self.my_dialog.exec_()
        #if not value:
            #self.button.setText(value)

class ProbeInterface(QDialog):
    '''
    '''
    probe_info_sgnl = pyqtSignal(object, str, str, int) # emit: probe_id, name, IP, probe_nbr. Warning: the first element is 'object' even though it should be an integer, but python id() function returns too big number to be encoded on 4-byte, which is the default for pyqtsignal int.

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ---
        self.retrunVal = None
        # ---  --- #
        self.probe_id  = kwargs.get('probe_id' , None)
        self.name      = kwargs.get('name'     , 'No name')
        self.IP        = kwargs.get('IP'       , 'No IP')
        self.probe_nbr = kwargs.get('probe_nbr', 1)
        # ---
        self.layout    = QGridLayout()
        self.setLayout(self.layout)

    def setUI(self):
        self.lineed_name = QLineEdit(self.name)
        self.lineed_IP   = QLineEdit(self.IP)
        self.CB_sonde    = QSpinBox()
        self.CB_sonde.setValue(self.probe_nbr)
        self.CB_sonde.setMinimum(1)
        self.CB_sonde.setMaximum(3)
        # ---  --- #
        self.layout.addWidget(QLabel('Probe ID: {}'.format(self.probe_id))   , 0, 0, 1, 2)
        self.layout.addWidget(self.lineed_name , 1, 0)
        self.layout.addWidget(QLabel('name')   , 1, 1)
        self.layout.addWidget(self.lineed_IP   , 2, 0)
        self.layout.addWidget(QLabel('IP')     , 2, 1)
        self.layout.addWidget(self.CB_sonde    , 3, 0)
        self.layout.addWidget(QLabel('probe nbr'), 3, 1)

    def setProbeInfo(self, ID, name, IP, probe_nbr):
        self.probe_id  = ID
        self.name      = name
        self.IP        = IP
        self.probe_nbr = probe_nbr

    def exec_(self):
        self.setUI()
        # ---  --- #
        super().exec_()
        return self.retrunVal

    def closeEvent(self, QCloseEvent):
        super().closeEvent(QCloseEvent)
        # ---
        self.name     = self.lineed_name.text()
        self.IP       = self.lineed_IP.text()
        self.probe_nbr= self.CB_sonde.value()
        # ---
        self.probe_info_sgnl.emit(self.probe_id, self.name, self.IP, self.probe_nbr)

##############################################################################################################
# MAIN
##############################################################################################################



if  __name__=="__main__":
    print('STARTING: Thermometer')
    myapp   = QApplication(sys.argv)
    app     = MainWindow()
    sys.exit(myapp.exec_())
    print('FINNISHED')
