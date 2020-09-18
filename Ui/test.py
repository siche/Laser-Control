
import socket
import time
from toptica_laser import toptica_laser as laser
"""
sock = socket.socket()
sock.connect(('192.168.1.61',1999))

for i in range(10):
    sock.send(("(query 'laser1:dl:pc:voltage-set)\r\n").encode('utf-8'))
    time.sleep(0.1)
    vol_str = sock.recv(256).decode('utf-8')
    print(len(vol_str))
    print(vol_str)
    print(vol_str[-21:-7])
"""
l1 = laser('192.168.1.61')
for i in range(10):
    print(l1.get_voltage())