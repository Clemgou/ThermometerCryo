# -*- coding: utf-8 -*-
#bash! /bin/env/python

##############################################################################################################
# IMPORTATION
##############################################################################################################

import numpy as np
import time, scipy
import scipy.optimize

from pathlib import Path, PureWindowsPath

import sys, os
sys.path.append('./')


from lib.Miscellaneous              import getIPFromTxt, fixpath
from lib.PyQt_miscellaneous         import QHLine, QVLine
from lib.Conversion_functions       import PT100_TvsR, ThermoBT_TvsR, ThermoNICO_TvsR, PT100_RvsT, C100_RvsT, RuO2_RvsT, ThermoBT_RvsT, ThermoHT_RvsT, ThermoNICOCAL_TvsR, ThermoBT_TvsR_spln
from lib.ResistanceProbe_class      import ResistanceProbe
from lib.MyRunningAnimation_class   import MyRunningAnimation
from lib.Buffer_class               import Buffer

import pyqtgraph                    as pg
import pyqtgraph.dockarea           as pg_dock
#import pyqtgraph.opengl as gl

import PyQt5
from PyQt5.QtWidgets    import QMainWindow, QWidget, QApplication, QPushButton, QToolButton, QStyle, QLabel, QCheckBox, QInputDialog, QComboBox, QFrame, QSpinBox, QDoubleSpinBox, QLineEdit, QTabWidget, QDockWidget, QFileDialog, QDialog
from PyQt5.QtWidgets    import QHBoxLayout, QVBoxLayout, QGridLayout, QSplitter   # main layouts
from PyQt5.QtGui        import QPixmap, QPaintDevice, QPainter, QIcon
from PyQt5.QtCore       import Qt, QSize

##############################################################################################################
# FUNCTION
##############################################################################################################

class MainWindow(QMainWindow):
    '''
    Main window of the application that embeds the ThermometerMonitoring widget.
    '''
    def __init__(self, **kwargs):
        super().__init__()
        self.verbose = kwargs.pop('verbose', False)
        # ---  --- #
        self.main_widget = ThermometerMonitoring(verbose=self.verbose, **kwargs)
        self.setCentralWidget(self.main_widget)
        # ---  --- #
        self.setWindowTitle("Cryostat thermometry")
        self.path_abs = os.path.dirname(os.path.abspath(__file__)) + '/'
        self.setWindowIcon(QIcon(self.path_abs+'icon.png'))
        self.setIconSize(QSize(32,32))
        self.show()

class ThermometerMonitoring(QWidget):
    '''
    * TO DO: cf README.txt
    * Some conventions:
        - the time is measured in epoch (nbr of seconds since 01/01/1970 at 00:00:00), but is saved in a txt in local date time (YYYY-MM-DD_hh:mm:ss).
        - the probes are identified by an ID number.
    '''
    def __init__(self, **kwargs):
        super().__init__()
        self.path_abs = os.path.dirname(os.path.abspath(__file__)) + '/'
        self.verbose  = kwargs.pop('verbose', False)
        IP_list       = kwargs.pop('IP'     , None) # must be a dictionnary such as: {IP_name1:'192.168.x.xx', IP_name2:'192.168.x.xx', ...}
        # ---  --- #
        self.date_time = '{0:04d}-{1:02d}-{2:02d}_{3:02d}:{4:02d}:{5:02d}'.format(*time.localtime()[:6])
        self.main_layout = QGridLayout()
        self.setLayout(self.main_layout) # setting the wrapper layout for the our widget
        # ---
        self.filename_dflt= 'Temp_evo_save_{0:d}_{1:02d}_{2:02d}'.format(*time.localtime()[:3]) # for automatique year_mounth_day filename
        self.probe_type_L = ["Mobile BT" , "Mobile HT" , "PT100" , "Mobile BM" , "NICO BT CAL"]
        self.N_buffer     = 50 # nbr of points in the local file data
        self.buffer_data  = {}
        self.fps          = 1 # Hz
        self.timer        = pg.QtCore.QTimer()
        self.isON         = False # bool for recordind state: True -> continuous recording, False -> no recording
        self.time_0       = self.getTime() # starting time in [s], which gives the reférence for the recording
        self.nbr_measure  = 0
        self.buffer_dflt  = -1
        self.color_pallet = {0:'r', 1:'g', 2:'b', 3:'c', 4:'m', 5:'y', 6:'w', 7:'#7f7f7f'} #can be changed, see mkColor in pyqtgraph API reference #color_dflt = {'blue':'#1f77b4','orange':'#ff7f0e','green':'#2ca02c','red':'#d62728','purple':'#9467bd','brown':'#8c564b','pink':'#e377c2','gray':'#7f7f7f','y-green':'#bcbd22','b-teal':'#17becf'}
        # ---
        if not IP_list:
            self.IP_dic   = getIPFromTxt(self.path_abs+'IPs_connection.txt')
        else:
            self.IP_dic   = IP_list
        # ---  --- #
        self.probes       = ResistanceProbe(verbose=self.verbose)
        id1 = self.probes.setProbe('Boite Mel'  , self.IP_dic['IP1'], 1)
        id2 = self.probes.setProbe('Bouilleur'  , self.IP_dic['IP1'], 2)
        id3 = self.probes.setProbe('Anneau 80mK', self.IP_dic['IP1'], 3)
        id4 = self.probes.setProbe('Etage   4 K', self.IP_dic['IP3'], 1)
        id5 = self.probes.setProbe('Etage  20 K', self.IP_dic['IP3'], 2)
        id6 = self.probes.setProbe('Etage 100 K', self.IP_dic['IP3'], 3)
        # ---
        self.makeBufferData()
        # ---
        self.probe_type_default = {id1:"Mobile BT"         ,id2:"Mobile BT"         ,id3:"Mobile BT"         ,id4:"Mobile HT"         ,id5:"Mobile HT"         ,id6:"PT100"}
        self.probe_color        = {id1:self.color_pallet[0],id2:self.color_pallet[1],id3:self.color_pallet[2],id4:self.color_pallet[3],id5:self.color_pallet[4],id6:self.color_pallet[5]}
        # ---  --- #
        self.setUI()
        # ---
        self.makeWidgetConnections()

    def setUI(self):
        self.layouts = {}
        self.layouts['layout_1'] = QVBoxLayout()
        self.layouts['layout_2'] = QSplitter(Qt.Horizontal)
        self.layouts['layout_3'] = QSplitter(Qt.Vertical)
        # ---  --- #
        #self.layouts['layout_2'].setFrameStyle(QFrame.Box | QFrame.Sunken) ; self.layouts['layout_2'].setLineWidth(2) ; self.layouts['layout_2'].setMidLineWidth(1)
        # ---  --- #
        self.makeTemperatureDisplayWidget()
        self.makeGraphWidget()
        self.makeTopBarWidget()
        self.makeImageWidget()
        # ---
        #self.makeAllGraph()
        # ---  --- #
        graph_dock_wdg = QDockWidget(self) # or graph_dock.setDockWidget(graph_dock_wdg)
        graph_dock_wdg.setWidget(self.graph_dic['main_wdg'])
        graph_dock_wdg.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable )#| QDockWidget.DockWidgetVerticalTitleBar)
        graph_dock     = QMainWindow(self)
        graph_dock.setDockNestingEnabled(True)
        graph_dock.addDockWidget(Qt.RightDockWidgetArea, graph_dock_wdg)
        # ---  --- #
        self.layouts['layout_1'].addWidget(self.topBar_dic['main_wdg'])
        self.layouts['layout_1'].addWidget(self.layouts['layout_2'])
        self.layouts['layout_2'].addWidget(self.image)
        self.layouts['layout_2'].addWidget(self.layouts['layout_3'])
        self.layouts['layout_3'].addWidget(self.makeTestConvertion())
        self.layouts['layout_3'].addWidget(self.tempDispl['main_wdg'])
        self.layouts['layout_3'].addWidget(graph_dock)
        # ---
        self.main_layout.addLayout(self.layouts['layout_1'], 0,0)

    def changeAllNameOfProbeId(self, probe_id, new_name):
        '''
        * Change the name of the probes everywhere it appears: checkboxes, in the legend of the graphs, etc ...
        '''
        self.tempDispl['Devices'][probe_id]['label'].setText(new_name)
        self.graph_dic['probes'][probe_id]['data'].opts.update( {'name':new_name} )
        # --- change name in check-box for the multiplot widget --- #
        for i, multiplot_name in enumerate(self.graph_dic['multiplots']):
            self.graph_dic['multiplots'][multiplot_name]['plot_choice_lab'][probe_id].setText(new_name)
        # --- change name of single plot Dock widget --- #
        self.graph_dic['probes'][probe_id]['wrapper'].setTitle(new_name)
        # --- change name in legends for the plotDataItems --- #
        self.graph_dic['probes'][probe_id]['graph'].getPlotItem().legend.items[0][1].setText(new_name)
        # --- multiplot
        for i, multiplot_name in enumerate(self.graph_dic['multiplots']):
            self.graph_dic['multiplots'][multiplot_name]['data_items'][probe_id].setData(name=new_name)

    def saveData(self, filename):
        '''
        Save the data of the resistance in an external file.
        The convention for a txt file is :
            time_1  probe_name_1  time_2  probe_name_2   time_3  probe_name_3 ...
            t1_0      R1_0         t2_0      R2_0         t3_0       R3_0 ...
                              .     .     .
        where the t_i are the time, and Ri_j are the measured resistance at ti_j.
        '''
        format_  = self.topBar_dic['Data_save_type'].currentText()
        path     = self.topBar_dic['save_dir_label'].text() + r'/'
        # --- check if directory exists
        if not os.path.isdir(path): # if directory does not exist because the date changed.
            os.mkdir(path)
        # --- check if file already exists --- #
        filename_L = os.listdir(path)
        # ---
        same_count = np.array([filename in fname_var for fname_var in filename_L]).sum() # check if a file has a filename contained in it.
        if same_count!=0:
            # ---
            filename  += '_{:d}'.format(same_count)
        elif self.topBar_dic['auto_save'].isChecked():
            filename  += '_{:d}'.format(0) # add _0 to the auto_save filename if none already exists.
        # ---
        path_to_file = '{}{}.{}'.format(path,filename,format_)
        # ---  --- #
        if format_ == 'txt':
            if not os.path.isfile(path_to_file): # if the file doesn't exist
                str_write  = '# filename={0}\n#time_start_date={1}, time_start_epoch={2}'.format(filename, self.date_time, self.time_0)
                str_write += '\n#'
                for i,key in enumerate(self.probes.probes):
                    str_write += 'time\t{0}(R)\t{1}(T)\t'.format(self.probes.probes[key]['name'].replace(' ', '_'), self.probes.probes[key]['name'].replace(' ', '_'))
                str_write += '\n'
            else:
                str_write = ''
            # ---  --- #
            with open(path_to_file, 'a+') as f:
                # ---  --- #
                for j in range(self.N_buffer):
                    for i,key in enumerate(self.probes.probes):
                        t_date = self.epochToDate(self.buffer_data[key]['buffer']['time'][j]) if self.buffer_data[key]['buffer']['time'][j]!=-1 else 'None'
                        str_write += '{0:}\t{1:}\t{2:}\t'.format(t_date, self.buffer_data[key]['buffer']['resistance'][j], self.buffer_data[key]['buffer']['temperature'][j])
                    # ---  --- #
                    str_write += '\n'
                # ---
                f.write(str_write+'\n')
        elif  format_ == 'asdf':
            pass

    def chooseNewDirectory(self, filedialog, label):
        new_path = filedialog.getExistingDirectory()
        os.chdir(new_path)
        # ---
        label.setText( new_path )

    def func_factory(self, func, *args):
        def f():
            func(*args)
        return f

    def makeWidgetConnections(self):
        self.timer.timeout.connect(self.update_record)
        # ---
        self.topBar_dic['play_bttn'].clicked.connect(self.startStop_continuous_record)
        self.topBar_dic['step_bttn'].clicked.connect(self.update_record)
        self.topBar_dic['fps_input'].valueChanged.connect(self.setFPS)
        self.topBar_dic['fps_input'].valueChanged.connect(self.setTimeWindowLabel)
        self.topBar_dic['save_dir_bttn'].clicked.connect( lambda : self.chooseNewDirectory(self.topBar_dic['save_dir'], self.topBar_dic['save_dir_label']) )
        self.topBar_dic['save_bttn'].clicked.connect( lambda : self.saveData(filename=self.topBar_dic['save_file'].text()) )
        # ---
        #self.tempDispl['Temp_thresh'].stateChanged.connect(self.setResistanceValue)
        #self.tempDispl['Temp_thresh'].stateChanged.connect(lambda: next(self.doConversionBuffer(self.tempDispl['Devices'][probe]) for probe in self.tempDispl['Devices']) )
        for i,probe_id in enumerate(self.tempDispl['Devices']):
            self.tempDispl['Devices'][probe_id]['resistance'].valueChanged.connect(       self.func_factory(self.doConversion      , probe_id))
            self.tempDispl['Devices'][probe_id]['probe_type'].currentIndexChanged.connect(self.func_factory(self.doConversion      , probe_id))
            self.tempDispl['Devices'][probe_id]['probe_type'].currentIndexChanged.connect(self.func_factory(self.doConversionBuffer, probe_id))
            self.tempDispl['Devices'][probe_id]['probe_type'].currentIndexChanged.connect(self.func_factory(self.toggleThreshButton, probe_id)) # enable/disable the threshold button
            self.tempDispl['Devices'][probe_id]['Temp_thresh'].stateChanged.connect(self.setResistanceValue)
            self.tempDispl['Devices'][probe_id]['Temp_thresh'].stateChanged.connect(self.func_factory(self.doConversionBuffer, probe_id) )
            # ---
            self.tempDispl['Devices'][probe_id]['label'].clicked.connect( self.func_factory(self.probes.exec_interface, probe_id) )
        # ---
        self.graph_dic['data_display'].currentIndexChanged.connect( self.updateGraphDisplayStyle )
        self.graph_dic['buffer_size'].valueChanged.connect(self.changeBufferSize)
        self.graph_dic['buffer_size'].valueChanged.connect(self.setTimeWindowLabel)
        # ---
        self.probes.interface.probe_info_sgnl.connect( lambda id,name,IP,probe_nbr: self.changeAllNameOfProbeId(id, name) )

    def makeBufferData(self):
        self.buffer_data['data_type'] = {'resistance':1, 'temperature':2}
        # ---  --- #
        for i,key in enumerate(self.probes.probes):
            self.buffer_data[key] = {'last'  : {'time':None, 'resistance':self.buffer_dflt},
                                     'buffer': {'time': Buffer([self.buffer_dflt]*self.N_buffer), 'resistance': Buffer([self.buffer_dflt]*self.N_buffer), 'temperature': Buffer([self.buffer_dflt]*self.N_buffer)}}

    def makeTopBarWidget(self):
        self.topBar_dic = {}
        self.topBar_dic['main_wdg']  = QWidget()
        self.topBar_dic['layout']    = QHBoxLayout()
        self.topBar_dic['play_bttn'] = QToolButton()#QPushButton('Play')
        self.topBar_dic['step_bttn'] = QPushButton('Single Measure')
        self.topBar_dic['state']     = MyRunningAnimation(type='pie_slice', draw_shape=[30,30])
        self.topBar_dic['fps_input'] = QDoubleSpinBox()
        # ---  --- #
        self.topBar_dic['save_bttn']      = QPushButton('Save plot data')
        self.topBar_dic['save_file']      = QLineEdit(self.filename_dflt)
        self.topBar_dic['save_file'].setMinimumWidth(200)
        self.topBar_dic['Data_save_type'] = QComboBox()
        self.topBar_dic['Data_save_type'].addItems(['txt', 'asdf (to do)'])
        self.topBar_dic['Data_save_type'].setMaximumWidth(80)
        self.topBar_dic['auto_save']      = QCheckBox()
        self.topBar_dic['auto_save'].setTristate(False)
        # ---
        self.topBar_dic['save_dir']       = QFileDialog()
        self.topBar_dic['save_dir_label'] = QLabel( str(self.topBar_dic['save_dir'].directory().path()) )
        self.topBar_dic['save_dir_label'].setWordWrap(True)
        self.topBar_dic['save_dir_bttn']  = QPushButton('&Dir:')
        self.topBar_dic['save_dir_bttn'].setMaximumWidth(50)
        # ---  --- #
        self.topBar_dic['play_bttn'].setMinimumWidth(75)
        self.topBar_dic['play_bttn'].setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.topBar_dic['play_bttn'].setStyleSheet("background-color: red")
        self.topBar_dic['step_bttn'].setStyleSheet("background-color: cyan")
        self.topBar_dic['fps_input'].setRange(0.001, 100)
        self.topBar_dic['fps_input'].setDecimals(3)
        self.topBar_dic['fps_input'].setMaximumWidth(100)
        self.topBar_dic['fps_input'].setValue(self.fps)
        # ---  --- #
        sublayout_1 = QHBoxLayout()
        sublayout_2 = QVBoxLayout()
        sublayout_1.addWidget(QLabel('Auto save : '))
        sublayout_1.addWidget(self.topBar_dic['auto_save'])
        sublayout_2.addLayout(sublayout_1)
        sublayout_2.addWidget(self.topBar_dic['save_bttn'])
        # ---
        self.topBar_dic['layout'].addWidget(self.topBar_dic['play_bttn'])
        self.topBar_dic['layout'].addWidget(self.topBar_dic['play_bttn'])
        self.topBar_dic['layout'].addWidget(self.topBar_dic['step_bttn'])
        self.topBar_dic['layout'].addWidget(self.topBar_dic['fps_input'])
        self.topBar_dic['layout'].addWidget(QLabel('fps'))
        self.topBar_dic['layout'].addWidget(QVLine())
        self.topBar_dic['layout'].addWidget(self.topBar_dic['state'])
        self.topBar_dic['layout'].addWidget(QVLine())
        self.topBar_dic['layout'].addLayout(sublayout_2)#.addWidget(self.topBar_dic['save_bttn'])
        self.topBar_dic['layout'].addWidget(QLabel('Save File :'))
        self.topBar_dic['layout'].addWidget(self.topBar_dic['save_file'])
        self.topBar_dic['layout'].addWidget(self.topBar_dic['Data_save_type'])
        self.topBar_dic['layout'].addWidget(self.topBar_dic['save_dir_bttn'])
        self.topBar_dic['layout'].addWidget(self.topBar_dic['save_dir_label'])
        # ---  --- #
        self.topBar_dic['main_wdg'].setLayout(self.topBar_dic['layout'])

    def makeImageWidget(self):
        self.image  = QLabel(self)
        pixmap      = QPixmap(self.path_abs+"cryoptics2.png")
        # ---  --- #
        #pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.FastTransformation)
        self.image.setScaledContents(True)
        self.image.setMinimumSize(10, 10)
        # ---  --- #
        self.image.setPixmap(pixmap)

    def makeTestConvertion(self):
        '''
        TemperatureDevice for setting manually the value of the resistance and check the temperature conversion
        '''
        dic         = self.makeTemperatureDevice("Manip", no_probe=True)
        layout      = QHBoxLayout()
        wdg_wrapper = QFrame()
        # ---  --- #
        for k, wdg_key in enumerate(dic):
            layout.addWidget(dic[wdg_key])
        # ---  --- #
        wdg_wrapper.setLayout(layout)
        return wdg_wrapper

    def makeTemperatureDisplayWidget(self):
        self.tempDispl               = {}
        self.tempDispl['main_wdg']   = QFrame()
        self.tempDispl['layout']     = QVBoxLayout()
        self.tempDispl['layout_grid']= QGridLayout()
        self.tempDispl['Devices']    = {}
        # ---  --- #
        #self.tempDispl['Devices']['Manip']       = self.makeTemperatureDevice("Manip")
        for i, probe_id in enumerate(self.probes.probes):
            self.tempDispl['Devices'][probe_id] = self.makeTemperatureDevice(probe_id)
        # ---
        for i,key in enumerate(self.tempDispl['Devices']):
            for k,wdg in enumerate(self.tempDispl['Devices'][key]):
                self.tempDispl['layout_grid'].addWidget(self.tempDispl['Devices'][key][wdg], i, k)
            # ---  --- #
            idx = self.tempDispl['Devices'][key]['probe_type'].findText(self.probe_type_default[key])
            self.tempDispl['Devices'][key]['probe_type'].setCurrentIndex(idx)
        # ---  --- #
        layout_inter = QHBoxLayout()
        # ---
        self.tempDispl['layout'].addLayout(layout_inter)
        self.tempDispl['layout'].addWidget(QHLine())
        self.tempDispl['layout'].addLayout(self.tempDispl['layout_grid'])
        self.tempDispl['layout'].addWidget(QHLine())
        # ---
        self.tempDispl['main_wdg'].setLayout(self.tempDispl['layout'])

    def makeTemperatureDevice(self, probe_id, no_probe=False):
        tempProb = {}
        # ---
        if no_probe:
            tempProb['label']        = QPushButton(probe_id)
            tempProb['label'].setCheckable(False)
        else:
            tempProb['label']        = QPushButton(self.probes.probes[probe_id]['name']) # the key of this tempProb element is still label because it is a modification of an old version where it was a QLabel and not a QPushButton
        # ---
        tempProb['resistance']   = QDoubleSpinBox()
        tempProb['label1']       = QLabel('Ohm')
        tempProb['temperature']  = QLineEdit()
        tempProb['label2']       = QLabel('K')
        tempProb['probe_type']   = QComboBox()
        tempProb['Temp_thr_lbl'] = QLabel('T > 70 K ')
        tempProb['Temp_thresh']  = QCheckBox()
        #tempProb['color']        = QComboBox()
        # ---  --- #
        tempProb['probe_type' ].addItems(self.probe_type_L)
        tempProb['temperature'].setReadOnly(True) # not necessary
        tempProb['temperature'].setMaximumWidth(100)
        tempProb['resistance' ].setRange(0, 1e6)
        tempProb['resistance' ].setDecimals(2)
        tempProb['resistance' ].setMaximumWidth(200)
        tempProb['resistance' ].setValue(500)
        tempProb['Temp_thresh'].setTristate(False)
        tempProb['Temp_thresh'].setCheckState(Qt.Checked) # Qt.Unchecked <-> 0 , Qt.PartiallyChecked <-> 1 , Qt.Checked <-> 2
        #tempProb['color' ].addItems(color_list)
        # ---  --- #
        #tempProb['label'].clicked.connect( self.func_factory(self.probes.exec_interface, probe_id) )
        #self.probes.interface.probe_info_sgnl.connect( lambda probe_id, name, IP, probe_nbr: tempProb['label'].setText(name) )
        #tempProb['resistance'].valueChanged.connect(lambda : self.doConversion(tempProb) )
        #tempProb['probe_type'].currentIndexChanged.connect(lambda : self.doConversion(tempProb) )
        #tempProb['probe_type'].currentIndexChanged.connect(lambda : self.doConversionBuffer(tempProb) )
        #tempProb['convert_bttn'].clicked.connect(lambda : self.doConversion(tempProb) )
        # ---  --- #
        return tempProb

    def makePlotWidget(self, key_probe, insert_plotData=True, plot_name=None):
        '''
        Generate a graph of the Temperature w.r.t time.
        '''
        plot_name  = self.probes.probes[key_probe]['name'] if not plot_name else None
        # ---  --- #
        graph_wdg  = pg.PlotWidget(title="")
        graph_nbr  = len(self.graph_dic['probes'].keys())
        graph_data = pg.PlotDataItem(name=plot_name)#, symbol='o')
        graph_viewbox  = graph_wdg.getViewBox()
        # ---  --- #
        graph_wdg.addLegend()
        if insert_plotData:
            graph_wdg.addItem(graph_data)
            graph_data.setPen(pg.mkColor(self.probe_color[key_probe])) # how to set linestyle as 'o-', ie continuous conection with dot at each vertices ??
        date_axis = pg.DateAxisItem()
        date_axis.utcOffset = time.altzone # account for timezone AND daylight (i.e summer or winter hours). It is equivalent to: time.timezone-time.daylight*3600
        graph_wdg.setAxisItems({'bottom': date_axis }) # to display date time from epoch convention. Attention !! it is not in local date time.
        graph_wdg.setLabel(axis='bottom',text='Time (UTC)'     )
        graph_wdg.setLabel(axis='left'  ,text='Temperature [K]')
        graph_wdg.showGrid(x=True,y=True)
        graph_viewbox.setAspectLocked(False)
        graph_viewbox.setRange(yRange=(0,+400))
        graph_viewbox.enableAutoRange(pg.ViewBox.XAxis, enable=True )
        graph_viewbox.enableAutoRange(pg.ViewBox.YAxis, enable=False)
        # ---  --- #
        return graph_wdg, graph_data

    def makeMultiPlotWidget(self, multiplot_name):
        '''
        * Generate a widget with a PlotWidget that will contains the different curve from PlotDataItem.
          However I haven't found a way to use the same PlotDataItem than for the single plots in the Tab widgets,
          because when we addItem in the multiplot PlotWidget, it removes the PlotDataItem from the previous widget.
        '''
        multiplot = {}
        multiplot['main_wdg']        = pg_dock.Dock(multiplot_name, closable=True)
        multiplot['layout']          = pg.LayoutWidget()#QHBoxLayout()
        graph_wdg, graph_data        = self.makePlotWidget(multiplot_name, plot_name=multiplot_name, insert_plotData=False) #pg.PlotWidget()
        multiplot['graph']           = graph_wdg
        multiplot['data_items']      = {}
        multiplot['plot_choice_wdg'] = QWidget()
        multiplot['plot_choice_lyt'] = QGridLayout()
        multiplot['plot_choice_box'] = {}
        multiplot['plot_choice_lab'] = {}
        wrapper = QSplitter(Qt.Horizontal)
        # ---  --- #
        for i,key in enumerate(self.probes.probes):
            multiplot['data_items'][key] = pg.PlotDataItem(name=self.probes.probes[key]['name'])
            multiplot['data_items'][key].setPen(pg.mkColor(self.probe_color[key]))
            # ---  --- #
            multiplot['plot_choice_lab'][key] = QLabel(self.probes.probes[key]['name'])
            multiplot['plot_choice_box'][key] = QCheckBox()
            multiplot['plot_choice_box'][key].setTristate(False)
            multiplot['plot_choice_box'][key].setCheckState(Qt.Unchecked) # Qt.Unchecked <-> 0 , Qt.PartiallyChecked <-> 1 , Qt.Checked <-> 2
            # ---  --- #
            multiplot['plot_choice_lyt'].addWidget(multiplot['plot_choice_lab'][key], i, 0)
            multiplot['plot_choice_lyt'].addWidget(multiplot['plot_choice_box'][key], i, 1)
            # ---  --- #
            multiplot['plot_choice_box'][key].stateChanged.connect( self.func_factory(self.setPlot, multiplot, key))#lambda: self.setPlot(multiplot, key) )
        # ---  --- #
        multiplot['plot_cscale'] = QComboBox()
        multiplot['plot_cscale'].addItems(['lin', 'log'])
        multiplot['plot_cscale'].currentIndexChanged.connect( lambda idx: self.changePlotScale(multiplot['graph'], idx) )
        multiplot['main_wdg'].sigClosed.connect( self.func_factory(self.closeMultiPlotWidget, multiplot_name) )
        # ---
        multiplot['plot_choice_lyt'].addWidget(multiplot['plot_cscale'], i+1, 0, 1, 2) # take i the last argument of the for loop
        # ---
        #wrapper.addWidget(multiplot['plot_choice_wdg'])
        #wrapper.addWidget(multiplot['graph'])
        #multiplot['layout'].addWidget(wrapper          , row=0, col=0)
        # ---  --- #
        multiplot['plot_choice_wdg'].setMaximumWidth(120) # does not work
        multiplot['layout'].addWidget(multiplot['plot_choice_wdg'], row=0, col=0)
        multiplot['layout'].addWidget(multiplot['graph']          , row=0, col=1)
        # ---  --- #
        multiplot['plot_choice_wdg'].setLayout(multiplot['plot_choice_lyt'])
        multiplot['main_wdg'].addWidget(multiplot['layout'])
        # ---  --- #
        return multiplot

    def makeGraphWidget(self):
        self.graph_dic = {}
        self.graph_dic['main_wdg']     = QFrame()
        self.graph_dic['layout']       = QVBoxLayout()
        self.graph_dic['top_bar']      = QHBoxLayout()
        self.graph_dic['dock_wdg']     = pg_dock.DockArea()
        self.graph_dic['multiplot_wdg']= pg_dock.DockArea()
        self.graph_dic['multiplots']   = {}
        # ---  --- #
        self.graph_dic['addmulti_bttn']= QPushButton('add Multiplot')
        self.graph_dic['addmulti_bttn'].clicked.connect(lambda: self.addMultiPlot(name='multiplot_{}'.format(len(self.graph_dic['multiplots'].keys()) )))
        self.graph_dic['display_type'] = QComboBox()
        self.graph_dic['display_type'].addItems(['Tab display','Multiplot', 'All in one'])
        self.graph_dic['data_display'] = QComboBox()
        self.graph_dic['data_display'].addItems(['temperature','resistance'])
        self.graph_dic['buffer_size']  = QSpinBox()
        self.graph_dic['buffer_size'].setRange(1, 1e5)
        self.graph_dic['buffer_size'].setMaximumWidth(200)
        self.graph_dic['buffer_size'].setValue(self.N_buffer)
        self.graph_dic['time_window']  = QLabel()
        self.setTimeWindowLabel()
        # ---  --- #
        self.graph_dic['probes']       = {}
        for i, probe_id in enumerate(self.tempDispl['Devices']):
            graph_wdg, graph_data = self.makePlotWidget(probe_id)
            self.graph_dic['probes'][probe_id] = {}
            self.graph_dic['probes'][probe_id]['graph'] = graph_wdg # store for future use
            self.graph_dic['probes'][probe_id]['data']  = graph_data
            # ---  --- #
            wrapper   = pg_dock.Dock(self.probes.probes[probe_id]['name'])
            wrapper.addWidget(self.graph_dic['probes'][probe_id]['graph'])
            self.graph_dic['probes'][probe_id]['wrapper'] = wrapper
            # ---  --- #
            self.graph_dic['dock_wdg'].addDock(wrapper, 'below')
        # ---  --- #
        self.addMultiPlot('multiplot_0')
        # ---  --- #
        self.graph_dic['top_bar'].addWidget(self.graph_dic['addmulti_bttn'])
        self.graph_dic['top_bar'].addWidget(QVLine())
        self.graph_dic['top_bar'].addWidget(QLabel('Display: '))
        self.graph_dic['top_bar'].addWidget(self.graph_dic['data_display'])
        self.graph_dic['top_bar'].addWidget(QVLine())
        self.graph_dic['top_bar'].addWidget(QLabel('   Buffer size: '))
        self.graph_dic['top_bar'].addWidget(self.graph_dic['buffer_size'])
        self.graph_dic['top_bar'].addWidget(QLabel('pts'))
        self.graph_dic['top_bar'].addWidget(QVLine())
        self.graph_dic['top_bar'].addWidget(QLabel('Time window:'))
        self.graph_dic['top_bar'].addWidget(self.graph_dic['time_window'])
        # ---  --- #
        top_bar_wrapper = QWidget()
        top_bar_wrapper.setLayout(self.graph_dic['top_bar'])
        top_bar_wrapper.setMaximumHeight(40)
        self.graph_dic['layout'].addWidget(top_bar_wrapper)
        sublayout = QSplitter(Qt.Horizontal)
        sublayout.addWidget(self.graph_dic['multiplot_wdg'])
        sublayout.addWidget(self.graph_dic['dock_wdg'])
        self.graph_dic['layout'].addWidget(sublayout)
        self.graph_dic['main_wdg'].setLayout(self.graph_dic['layout'])

    def makeAllGraph(self):
        '''
        '''
        for i, key in enumerate(self.tempDispl['Devices']):
            self.graph_dic['tab_wdg'].addTab(self.graph_dic['probes'][key]['graph'], key)

    def update_record(self):
        self.nbr_measure += 1
        # ---  --- #
        self.measureResistance()
        self.setResistanceValue()
        self.updateGraphs()
        # ---  --- #
        self.topBar_dic['state'].nextState()
        # ---  --- #
        if self.nbr_measure==self.graph_dic['buffer_size'].value():
            self.nbr_measure = 0
            # ---
            if self.topBar_dic['auto_save'].isChecked():
                print( 'Auto-save at : {0:04d}-{1:02d}-{2:02d}_{3:02d}:{4:02d}:{5:02d}'.format(*time.localtime(time.time())[:6]) )
                # ---
                self.saveData( filename='auto_save_{0:04d}-{1:02d}-{2:02d}'.format(*time.localtime(time.time())[:3]) )

    def updateGraphDisplayStyle(self, idx):
        '''
        '''
        if   idx==0: # Temperature
            self.display_buffer_idx = 2
            # ---
            for i, key in enumerate(self.tempDispl['Devices']):
                graph_wdg = self.graph_dic['probes'][key]['graph']
                # ---  --- #
                graph_wdg.setLabel(axis='left'  ,text='Temperature [K]')
                graph_viewbox  = graph_wdg.getViewBox()
                graph_viewbox.setRange(yRange=(0,+400))
            for i, key in enumerate(self.graph_dic['multiplots']):
                graph_wdg = self.graph_dic['multiplots'][key]['graph']
                # ---  --- #
                graph_wdg.setLabel(axis='left'  ,text='Temperature [K]')
                graph_viewbox  = graph_wdg.getViewBox()
                graph_viewbox.setRange(yRange=(0,+400))
        elif idx==1: # Resistance
            self.display_buffer_idx = 1
            # ---
            for i, key in enumerate(self.tempDispl['Devices']):
                graph_wdg = self.graph_dic['probes'][key]['graph']
                # ---  --- #
                graph_wdg.setLabel(axis='left'  ,text='Resistance [Ohm]')
                graph_viewbox  = graph_wdg.getViewBox()
                graph_viewbox.setRange(yRange=(0,+10000))
            for i, key in enumerate(self.graph_dic['multiplots']):
                graph_wdg = self.graph_dic['multiplots'][key]['graph']
                # ---  --- #
                graph_wdg.setLabel(axis='left'  ,text='Resistance [Ohm]')
                graph_viewbox  = graph_wdg.getViewBox()
                graph_viewbox.setRange(yRange=(0,+10000))

    def changePlotScale(self, plot_wdg, idx):
        if   idx==0:
            plot_wdg.setLogMode(x=False, y=False)
        elif idx==1:
            plot_wdg.setLogMode(x=False, y=True)

    def setPlot(self, multiplot, probe_key):
        # ---  --- #
        if multiplot['plot_choice_box'][probe_key].isChecked():
            #multiplot['data_items'][probe_key].setVisible(True)
            multiplot['graph'].addItem(   multiplot['data_items'][probe_key])
        else:
            #multiplot['data_items'][probe_key].setVisible(False)
            multiplot['graph'].removeItem(multiplot['data_items'][probe_key])

    def addMultiPlot(self, name):
        self.graph_dic['multiplots'][name] = self.makeMultiPlotWidget(name)
        self.graph_dic['multiplot_wdg'].addDock(self.graph_dic['multiplots'][name]['main_wdg'])

    def closeMultiPlotWidget(self, multiplot_name):
        layout_wdg = self.graph_dic['multiplots'][multiplot_name]['main_wdg'].widgets[0]
        # ---  --- #
        for i in reversed(range(layout_wdg.layout.count())):
            wdg = layout_wdg.layout.itemAt(i).widget()
            wdg.deleteLater()
            wdg.setParent(None)
            print('Deleting widget: ', wdg) if self.verbose else None
        # ---  --- #
        for key, data_item in self.graph_dic['multiplots'][multiplot_name]['data_items'].items():
            data_item.deleteLater()
            data_item.setParent(None)
            print('Deleting data item: ', data_item) if self.verbose else None
        # ---  --- #
        del self.graph_dic['multiplots'][multiplot_name]

    def getTime(self):
        '''
        * Returns the time in the app convention
        '''
        #return time.mktime(time.localtime())+round(time.time()%1, 3)
        return round(time.time(), 3)

    def epochToDate(self, t_epoch):
        '''
        * Convert an epoch time number to a readable date in YYYY-MM-DD_hh:mm:ss:msss
          format.
        '''
        return '{0:04d}-{1:02d}-{2:02d}_{3:02d}:{4:02d}:{5:02d}:{6:03d}'.format(*time.localtime(t_epoch)[:6], int((t_epoch%1) * 1e3))

    def measureResistance(self):
        for i, probe_id in enumerate(self.probes.probes):
            res = self.probes.getRESISTANCE(ID=probe_id)
            t_  = self.getTime()#-self.time_0
            # ---  --- #
            if not res: # if res is None, i.e measure did not work
                #print('[{:s}] Error in measureResistance: measure of resistance did not work, returning a random value around 500 Ohm.'.format( self.epochToDate(time.time())[:-4] ))
                print('[{:s}] Error in measureResistance: measure of resistance did not work, returning last measrued value.'.format( self.epochToDate(time.time())[:-4] ))
                res  = self.buffer_data[probe_id]['last']['resistance'] # 500 + np.random.random()*10
            # ---  --- #
            temp = self.convertResToTemp(res, type=self.tempDispl['Devices'][probe_id]['probe_type'].currentText(), above70K=self.tempDispl['Devices'][probe_id]['Temp_thresh'].isChecked())
            # ---  --- #
            self.buffer_data[probe_id]['last'  ]['resistance']  = res
            self.buffer_data[probe_id]['last'  ]['time'      ]  = t_
            # ---
            self.buffer_data[probe_id]['buffer']['time'       ].push_element(t_)
            self.buffer_data[probe_id]['buffer']['resistance' ].push_element(res)
            self.buffer_data[probe_id]['buffer']['temperature'].push_element(temp)
        # ---  --- #
        self.setResistanceValue()

    def setResistanceValue(self):
        for i,key in enumerate(self.tempDispl['Devices']):
            res_val = self.buffer_data[key]['last']['resistance']
            if res_val: # equivalent to 'if res_val is not None'
                self.tempDispl['Devices'][key]['resistance'].setValue(res_val)
                # ---
                self.doConversion(key)

    def doConversion(self, probe_id):
        probe_type = self.tempDispl['Devices'][probe_id]['probe_type'].currentText()
        # ---  --- #
        Temp_K = self.convertResToTemp(self.tempDispl['Devices'][probe_id]['resistance'].value(), type=probe_type, above70K=self.tempDispl['Devices'][probe_id]['Temp_thresh'].isChecked())
        # ---
        self.tempDispl['Devices'][probe_id]['temperature'].setText('{:.4f}'.format(Temp_K))

    def doConversionBuffer(self, probe_id):
        '''
        * Convert all res to temp from buffer.
        '''
        # ---  --- #
        for i,val in enumerate(self.buffer_data[probe_id]['buffer']['resistance']):
            if val!=self.buffer_dflt:
                self.buffer_data[probe_id]['buffer']['temperature'][i] = self.convertResToTemp(val, type=self.tempDispl['Devices'][probe_id]['probe_type'].currentText(), above70K=self.tempDispl['Devices'][probe_id]['Temp_thresh'].isChecked())
        # ---  --- #
        self.updateGraphs()

    def toggleThreshButton(self, probe_id):
        '''
        * Enable/Disable the threshold > 70K button for the probes that does not
          need it.
        * The probes that are in need of it are: "Mobile BT", "Mobile HT".
        * One can check in the 'convertResToTemp' method.
        '''
        if self.tempDispl['Devices'][probe_id]['probe_type' ].currentText() in ["Mobile BT", "Mobile HT"]:
            self.tempDispl['Devices'][probe_id]['Temp_thresh'].setEnabled(True)
        else:
            self.tempDispl['Devices'][probe_id]['Temp_thresh'].setEnabled(False)

    def convertResToTemp(self, res, **kwargs):
        '''
        From the kwargs arguments, will return the temperature corresponding to the right probe parameters,
        and the threshold of the 70K.
        '''
        probe_type = kwargs.pop('type'    , None)
        above70K   = kwargs.pop('above70K', None)
        # ---  --- # self.probe_type_L = ["Mobile BT","Mobile HT","NICO BT","PT100", "Mobile BM"]
        if not probe_type in self.probe_type_L:
            print('Error: in convertResToTemp, the probe type is not valid.')
            return None
        # ---  --- #
        if   probe_type in ["Mobile BT"]: # reference BT RuO2 C100 PT100, (pour le moment, ne l'utiliser qu'a haute temperature)
            #try:
            #    T = scipy.optimize.newton( (lambda T:ThermoBTRvsT(T)-res) , 200 if above70K else 0.02)
            #except RuntimeError:
            #    print('RuntimeError in convertResToTemp: no value found with scipy.optimize.newton.')
            #    T = 500
            ## ---
            T = ThermoBT_TvsR_spln(res, above70K=above70K)
        elif probe_type in ["Mobile HT"]: # reference HT C100-PT100
            try:
                T = scipy.optimize.newton( (lambda T:ThermoHT_RvsT(T)-res) , 200 if above70K else 2)
            except RuntimeError:
                print('RuntimeError in convertResToTemp: no value found with scipy.optimize.newton.')
                T = 500
        elif probe_type in ["NICO BT CAL"]: # Thermo NICO
            T = ThermoNICOCAL_TvsR(res)
        elif probe_type in ["NICO BT"]: # Thermo NICO
            T = ThermoNICO_TvsR(res)
        elif probe_type in ["PT100"]: # PT100 seule
            T = PT100_TvsR(res)
        elif probe_type in ["Mobile BM"]: # Mobile BM BT RuO2 C100 PT100, (a utiliser uniquement a basse temperature pour les thermometres mobiles)
            T = ThermoBT_TvsR(res)
        # ---  --- #
        return T

    def toggle_continuous_record_qtimer(self, state):
        # ---  --- #
        if   state=='start':
            self.timer.start(int(1e3/self.fps)) # [ms]
        elif state=='stop':
            self.timer.stop()

    def startStop_continuous_record(self):
        if  self.isON:
            self.toggle_continuous_record('stop')
            self.topBar_dic['play_bttn'].setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            self.topBar_dic['play_bttn'].setStyleSheet("background-color: red")
            self.topBar_dic['step_bttn'].setFlat(False)
            self.topBar_dic['step_bttn'].setEnabled(True)
        else:
            self.toggle_continuous_record('start')
            self.topBar_dic['play_bttn'].setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
            self.topBar_dic['play_bttn'].setStyleSheet("background-color: green")
            self.topBar_dic['step_bttn'].setFlat(True)
            self.topBar_dic['step_bttn'].setEnabled(False)

    def toggle_continuous_record(self, state):
        '''
        '''
        if   state=='start':
            self.toggle_continuous_record_qtimer(state)
            self.isON = True
        elif state=='stop':
            self.toggle_continuous_record_qtimer(state)
            self.isON = False

    def setFPS(self):
        self.fps = self.topBar_dic['fps_input'].value()
        self.timer.setInterval(int(1e3/self.fps))

    def changeBufferSize(self, new_size):
        self.N_buffer = int(new_size)
        # ---  --- #
        for i,key in enumerate(self.probes.probes):
            self.buffer_data[key]['buffer']['time'       ].change_length(self.N_buffer, default_val=self.buffer_dflt)
            self.buffer_data[key]['buffer']['resistance' ].change_length(self.N_buffer, default_val=self.buffer_dflt)
            self.buffer_data[key]['buffer']['temperature'].change_length(self.N_buffer, default_val=self.buffer_dflt)

    def setTimeWindowLabel(self):
        t_wind = self.N_buffer/self.fps
        self.graph_dic['time_window'].setText('{0:02d}h{1:02d}min{2:02d}s'.format(int(t_wind//3600), int((t_wind%3600)//60), int((t_wind%60)//1)))

    def updateGraphs(self):
        which_data  = self.graph_dic['data_display'].currentText()
        for i, key in enumerate(self.probes.probes):
            display_idx = self.N_buffer - np.where(np.array(self.buffer_data[key]['buffer']['time'])==self.buffer_dflt)[0].size # only for display effect, avoid displaying the default value when the buffer is not full of data
            xdata = self.buffer_data[key]['buffer']['time'    ][-display_idx:]
            ydata = self.buffer_data[key]['buffer'][which_data][-display_idx:]
            # ---  --- #
            self.graph_dic['probes'][key]['data'].setData(x=np.array(xdata)[~np.isnan(ydata)], y=np.array(ydata)[~np.isnan(ydata)])
            # ---  --- #
            for name, multiplot in self.graph_dic['multiplots'].items():
                multiplot['data_items'][key].setData(x=self.graph_dic['probes'][key]['data'].xData,
                                                     y=self.graph_dic['probes'][key]['data'].yData)

##############################################################################################################
# MAIN
##############################################################################################################

if  __name__=="__main__":
    print('STARTING: Thermometer')
    myapp   = QApplication(sys.argv)
    app     = MainWindow(verbose=False, IP={'IP1':'192.168.1.101','IP3':'192.168.1.103'})
    sys.exit(myapp.exec_())
    print('FINNISHED')
