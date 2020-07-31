# -*- coding: utf-8 -*-
#bash! /bin/env/python

##############################################################################################################
# IMPORTATION
##############################################################################################################

import numpy as np
import time
import sys, os

from PyQt5 import QtNetwork

##############################################################################################################
# FUNCTION
##############################################################################################################

class Buffer(list):
    '''
    Class that behaves like a buffer.
    Inherit from list object in python.
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def push_element(self, elmt):
        self[:] = self[1:]+[elmt]
        return self

    def change_length(self, new_len, **kwargs):
        default_val = kwargs.pop('default_val', None)
        # ---  --- #
        curr_len = len(self)
        # ---
        if curr_len>=new_len:
            self[:] = self[-new_len:]
        else:
            self[:] = [default_val]*(new_len-curr_len) + self[:]
        # ---  --- #
        return self
    '''
    Trying to modify list class method in order to conserve the Buffer class when we make operation on the lists.
    Indeed even if Buffer inherite from list class, when we make operation such as: Buffer[slice1] +  Buffer[slice2],
    it will return a list object type, because the operator '+' defined in the list class returns a list object.
    Eg:     buffer = Buffer( [i for i in range(10)] )
            print(type(buffer))    --> <class '__main__.Buffer'>
            print(type(buffer[:])) --> <class 'list'>
    However, using the '[:]' seems to circonvene the problem without redefining the add operator.

    def __add__(self, x):
        return self.__class__(super().__add__(x))

    def __getitem__(self, i):
        res = super().__getitem__(i)
        return self.__class__(res) if isinstance(res, list) else res
    '''

##############################################################################################################
# MAIN
##############################################################################################################

if  __name__=="__main__":
    print('STARTING: Thermometer')
    list_  = [i for i in range(10)]
    buffer = Buffer(list_)
    print(buffer)
    print(type(buffer))
    print(type(buffer[:]))
    buffer.push_element('hello world')
    buffer.push_element(23)
    print(buffer)
    buffer.change_length(5)
    print(buffer)
    buffer.change_length(15)
    print(buffer)
    print('FINNISHED')
