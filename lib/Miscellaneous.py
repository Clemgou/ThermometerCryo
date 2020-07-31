# -*- coding: utf-8 -*-
#bash! /bin/env/python

##############################################################################################################
# IMPORTATION
##############################################################################################################



##############################################################################################################
# FUNCTION
##############################################################################################################

def getIPFromTxt(path_to_file):
    '''
    Go to a txt file at path_to_file and returns a dictionary of IP addresses in the file.
    In the txt file we expect to have the data in the form:
        IP_name = 'IP_address' (# comments)
    where the parenthesis indicates non necessary features.
    '''
    IP_dic = {}
    # ---  --- #
    with open(path_to_file, 'r') as f:
        a = f.read().splitlines()
        for line in a:
            key = line.split('=')[0].replace(' ','')
            val = line.split('=')[1].split('#')[0].replace(' ','').replace('"','').replace("'","")
            # ---
            IP_dic[key] = val
    #---  --- #
    return IP_dic

##############################################################################################################
# MAIN
##############################################################################################################

if __name__=='__main__':
    print('STARTING')
    print('FINNISHED')
