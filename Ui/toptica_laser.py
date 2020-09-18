# -*- coding: utf-8 -*-
"""
this class represents the Toptica DLC pro laser controller
"""

import socket
import time
         
class toptica_laser(object):
    
    def __init__(self, ip_address, timeout = 3, port = 1998):
        
        self.ip_address = ip_address
        self.port = port
        self.timeout = timeout
        self.get_lock = False
        self.set_lock = False
        
        try:
            self._socket_get = socket.socket()
            self._socket_set = socket.socket()
            self._socket_get2 = socket.socket()

            if timeout is not None:
                self._socket_get.settimeout(timeout)
                self._socket_set.settimeout(timeout)
                self._socket_get2.settimeout(timeout)

            self._socket_set.connect((ip_address, port))
            self._socket_get.connect((ip_address, port+1))
            self._socket_get2.connect((ip_address, port+1))
            
            print('Toptica DLC pro at ip address ' + str(self.ip_address) + ' is online')
            time.sleep(0.5)

        except socket.error as e:
            print('connection to Toptica DLC pro at address' + str(ip_address) + ' FAILED!')
        
        # check for system health and print the response
        self._socket_set.send(("(param-ref 'system-health-txt)" + "\r\n").encode('utf-8'))

        # clear possible return value
        time.sleep(0.1) 
        self._socket_set.recv(256)
        self._socket_get.recv(1024)
        self._socket_get2.recv(1024)

            
    def set_parameter(self, command, param):
        
        success = self._socket_set.send(("(param-set! '" + str(command) + " " + str(param) + ")" + "\r\n").encode('utf-8'))
        value = self._socket_set.recv(256)
        
        return success
    
    def read_parameter(self, command):
        # send request
        while True:
            try:
                self._socket_get.send(("(query '" + command + ")" + "\r\n").encode('utf-8'))
            
                # wait and receive answer
                find_str = command[-10:]
                time.sleep(0.01)
                value = self._socket_get.recv(256).decode('utf-8')
                start = value.find(find_str)+len(find_str)+1
                return float(value[start:-1])
            except:
                print('Read Failed')

    def test(self,command):
        self._socket_get.send(("(query '"+command+')'+'\r\n').encode('utf-8')) 
        time.sleep(0.05)
        return(self._socket_get.recv(1024).decode('utf-8')) 

    def get_voltage(self):
        while True:
            try:
                self._socket_get.send(("(query 'laser1:dl:pc:voltage-set)\r\n").encode('utf-8'))
                time.sleep(0.05)
                vol_str = self._socket_get.recv(1024).decode('utf-8')
                start = vol_str.find('set')+4
                # print(vol_str)
                return float(vol_str[start:-3])
                # print(vol)
            except Exception as e:
                print(e)
                print('Get voltage Failed, Retrying ...')
                time.sleep(0.1)
        
    def set_voltage(self, vol):
        flag = False
        while not flag:
            temp = self.set_parameter('laser1:dl:pc:voltage-set', vol)
            flag = (temp==0 or temp>0)
            # print('set_voltage:%s' % flag)
            time.sleep(0.05)

    def get_status(self):
        while True:
            try:
                status = self._socket_get2.send(("(query 'laser1:emission)\r\n").encode('utf-8'))
                time.sleep(0.05)
                status = self._socket_get2.recv(1024).decode('utf-8')

                # print(status)
                # print(status[-4:-3])
                return (status[-4:-3]=='t')
                # print('Status:%s, len:%d' % (status, len(status)))
            except:
                time.sleep(0.05)

        return (status == '#t') 
    
    """ it seem that DLC pro does not support control of physical button
    def on(self):
        self.set_parameter('emission-button-enabled',1)
        time.sleep(0.1)
        if self.get_status():
            print('laser is on')
        else:
            print('enable emission failed')
    
    def off(self):
        self.set_parameter('emission-button-enabled',0)
        time.sleep(0.1)
        if not self.get_status():
            print('laser is off')
        else:
            print('enable emission failed')


    def off(self):
        self.
    """
    @property
    def status(self):
        return (self.get_status())
    

    def lock(self,current_fre, des_fre):
        k_p = -0.1
        # k_i = 0
        # k_d = 0
        delta_vol = k_p*(des_fre-current_fre)*1000
        while (delta_vol > 0.5 or delta_vol < -0.5):
            print('volatge gap is too big, please check data setting')
            delta_vol = delta_vol/2
        # print(self.get_voltage())
        new_vol = delta_vol + self.get_voltage()
        self.set_voltage(new_vol)