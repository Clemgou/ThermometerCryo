# -*- coding: utf-8 -*-
#bash! /bin/env/python

##############################################################################################################
# IMPORTATION
##############################################################################################################

import numpy as np
import time
import sys, os

from PyQt5 import QtNetwork

try:
	from ProbeInterface_class import ProbeInterface
except:
	sys.path.append("../")
	from lib.ProbeInterface_class import ProbeInterface


##############################################################################################################
# FUNCTION
##############################################################################################################

class ResistanceProbe():
    '''
    Class to address the probes that measure the resistance.
    '''
    def __init__(self, **kwargs):
        self.verbose = kwargs.pop('verbose', False)
        # ---  --- #
        self.data = None
        self.UDP_query = QtNetwork.QUdpSocket()      # le canal sur lequel on envoie les demandes
        self.UDP_resp  = QtNetwork.QUdpSocket()     # le canal de lecture
        # ---  --- #
        udp_q_bound_success = self.UDP_query.bind(8001)
        udp_r_bound_success = self.UDP_resp.bind(12000)
        print('UDP query    channel binding: ', udp_q_bound_success) if self.verbose else None
        print('UDP response channel binding: ', udp_r_bound_success) if self.verbose else None
        # ---  --- #
        #self.UDP_query.readyRead.connect( lambda: self.processPendingDatagrams(self.UDP_resp) )
        # ---  --- #
        self.interface = ProbeInterface()
        self.probes    = {}
        self.default_resistance = 500 # just for debugging
        # ---  --- #
        self.interface.probe_info_sgnl.connect(self.changeProbeInfo)

    def exec_interface(self, probe_id):
        self.interface.setProbeInfo(ID=probe_id, name=self.probes[probe_id]['name'], IP=self.probes[probe_id]['IP'], probe_nbr=self.probes[probe_id]['probe_nbr'])
        self.interface.exec_()

    def setProbe(self, name, IP, nbr):
        probe_dic             = {'name':name, 'IP':IP, 'probe_nbr':nbr}
        id_probe              = id(probe_dic)
        self.probes[id_probe] = probe_dic
        # ---
        return id_probe

    def changeProbeInfo(self, probe_id, name, IP, probe_nbr):
        self.probes[probe_id].update( {'name':name, 'IP':IP, 'probe_nbr':probe_nbr} )

    def getRESISTANCE(self, **kwargs):
        '''
        Function that connect to the MacRT server and request the resistance measured by 'sonde' at the IP addres 'IP'.
        Returns the resistance measure by 'sonde'.
        * Arguments:
            - IP, is string ip address in the form '192.168.1.xxx'
            - sonde, is an integer that indicates the probes to ask
        '''
        id    = kwargs.pop('ID'   , None)
        IP    = kwargs.pop('IP'   , None)
        sonde = kwargs.pop('sonde', None)
        # ---  --- #
        if id:
            try:
                IP    = self.probes[id]['IP']
                sonde = self.probes[id]['probe_nbr']
            except KeyError:
                pass
        # ---
        else:
            if IP==None or sonde==None:
                print('Error: in getRESISTANCE, wrong arguments, cannot find the IP or the sonde number.')
                return None
        # ---  --- #
        self.resistance = None # initiate the resistance value at None in case the query doesn't work, so that we don't have an old value.
        # ---  --- #
        query = "MACRTGET {0}".format((sonde-1)*11+3)
        port = 12000 +int(IP[-3:], 10)
        try:
            print(query, IP, port) if self.verbose else None
            out_ = self.UDP_query.writeDatagram(query.encode(), QtNetwork.QHostAddress(IP), port)
            print(out_) if self.verbose else None
            time.sleep(0.1) # for not overloading the query-response
            self.processPendingDatagrams(self.UDP_resp)
        except:
            print('Connection error, cannot retrieve resistance data.')
            return None
        # ---  --- #
        return self.resistance

    def processPendingDatagrams(self, udpSocket):
        while udpSocket.hasPendingDatagrams():
            datagram, host, port = udpSocket.readDatagram(udpSocket.pendingDatagramSize())
            self.data = datagram.decode().strip().split()
            # ---  --- #
            self.resistance = float(self.data[2])

##############################################################################################################
# MAIN
##############################################################################################################

if  __name__=="__main__":
    print('STARTING: Thermometer')
    IP_dic       = {'IP1':'192.168.1.101', 'IP3':'192.168.1.103'}
    probes       = ResistanceProbe(verbose=True)
    probes.setProbe('Boite Mel', IP_dic['IP1'], 1)
    res = probes.getRESISTANCE(name='Boite Mel')
    print(res)
    print('FINNISHED')
