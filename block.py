#!/usr/local/bin/python

import socket

s = socket.socket()

port = 49538
s.connect(('127.0.0.1', port))
s.close()        

#print("hello", file=open("C:\\project\\test\\fileName.txt","a"))