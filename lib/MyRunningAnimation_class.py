# -*- coding: utf-8 -*-
#bash! /bin/env/python

##############################################################################################################
# IMPORTATION
##############################################################################################################

import sys, os
sys.path.append('./')

import pyqtgraph as pg

import PyQt5
from PyQt5.QtWidgets    import QMainWindow, QWidget, QApplication, QPushButton, QLabel, QCheckBox, QInputDialog, QComboBox, QFrame, QSpinBox, QDoubleSpinBox, QLineEdit, QTabWidget, QDockWidget, QFileDialog
from PyQt5.QtWidgets    import QHBoxLayout, QVBoxLayout, QGridLayout, QSplitter   # main layouts
from PyQt5.QtGui        import QPixmap, QPaintDevice, QPainter, QPen, QBrush, QColor, QPainterPath
from PyQt5.QtCore       import QRect, QRectF

my_colors = {'black':'#151b25', 'blue':'#034687', 'green':'#10bc10', 'red':'#e12a2a', 'grey':'#bdc3c7'} # hexadecimal definition of color

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
        self.main_widget = MyRunningAnimation(type='pie_slice', draw_shape=[100,100])
        self.setCentralWidget(self.main_widget)
        # ---  --- #
        self.timer          = pg.QtCore.QTimer()
        self.fps            = 1 # Hz
        self.timer.start(int(1e3/self.fps))
        # ---
        self.timer.timeout.connect(self.main_widget.nextState)
        # ---  --- #
        self.show()

class MyRunningAnimation(QWidget):
    def __init__(self, type='pie_sice', draw_shape=[10,10]):
        super().__init__()
        self.anim_type = type # Specify the type of animation: 'pie_sice' , 'rectangle'
        # ---  --- #
        self.color_active   = QColor(my_colors['green'])
        self.color_inactive = QColor(my_colors['black'])
        self.pen            =   QPen(self.color_active)
        self.brush          = QBrush(self.color_inactive)
        # ---
        self.item_nbr       = 8
        self.draw_shape     = draw_shape
        # ---  --- #
        if   self.anim_type=='rectangle':
            self.setRectangleItems()
            self.paintState = self.rectangleAnimation
        elif self.anim_type=='pie_slice':
            self.setPieSliceItems()
            self.paintState = self.pieSliceAnimation
        # ---  --- #
        self.setMinimumWidth( self.draw_shape[0])
        self.setMinimumHeight(self.draw_shape[1])
        # ---  --- #
        self.current_active = 0

    def paintEvent(self, event): # the method name is important ! As 'paintEvent' is called when the QWidget class is modified by the application
        painter = QPainter(self) # recupere le QPainter du widget
        painter.setRenderHints(QPainter.Antialiasing)
        # ---  --- #
        self.pen.setWidth(1)
        painter.setPen(self.pen)
        painter.setBrush(self.brush)
        # ---  --- #
        self.paintState(painter)

    def nextState(self):
        self.current_active = (self.current_active + 1)%self.item_nbr
        # ---  --- #
        self.update() # relaunch paintEvent

    def setRectangleItems(self):
        width  = int( self.draw_shape[0]/self.item_nbr )
        height = self.draw_shape[1]
        # ---  --- #
        self.rect_dic       = {}
        for i in range(self.item_nbr):
            self.rect_dic['rect_{:d}'.format(i)] = QRect(i*width, 0, width, height)

    def setPieSliceItems(self):
        self.span_angle = int( (360)/self.item_nbr ) # in [deg]
        width      = self.draw_shape[0] - 2 # '-2' because there is a small negative offset due to antialiasing, noticible with small draw_shape
        height     = self.draw_shape[1] - 2 # '-2' because there is a small negative offset due to antialiasing, noticible with small draw_shape
        bound_rect = QRectF(1, 1, width, height)
        center     = PyQt5.QtCore.QPointF(bound_rect.width()/2 +1, bound_rect.height()/2 +1)
        # ---  --- #
        self.slice_dic  = {}
        for i in range(self.item_nbr):
            start_angle = -i*self.span_angle
            # ---
            path_slice_i = QPainterPath()
            path_slice_i.moveTo(center)
            path_slice_i.arcTo(bound_rect , start_angle,self.span_angle)
            # ---  --- #
            self.slice_dic['slice_{:d}'.format(i)] = path_slice_i

    def rectangleAnimation(self, painter):
        for i in range(self.item_nbr):
            painter.drawRect(self.rect_dic['rect_{:d}'.format(i)])
        # ---  --- #
        painter.fillRect(self.rect_dic['rect_{:d}'.format(self.current_active)], QBrush(self.color_active))

    def pieSliceAnimation(self, painter):
        for i in range(self.item_nbr):
            painter.drawPath(self.slice_dic['slice_{:d}'.format(i)])
        # ---  --- #
        painter.fillPath(self.slice_dic['slice_{:d}'.format(self.current_active)], QBrush(self.color_active))

##############################################################################################################
# MAIN
##############################################################################################################



if  __name__=="__main__":
    print('STARTING: Thermometer')
    myapp   = QApplication(sys.argv)
    app     = MainWindow()
    sys.exit(myapp.exec_())
    print('FINNISHED')
