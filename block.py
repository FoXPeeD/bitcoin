#!/usr/bin/python3.7

import socket
import os

s = socket.socket()
port = 49538
junk = s.connect(('10.0.2.100', port))
s.close()
