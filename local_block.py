#!/usr/bin/python3.7

import socket
import os

s = socket.socket()
port = 49538
s.connect(('127.0.0.1', port))
s.close()
