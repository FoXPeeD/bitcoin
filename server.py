# first of all import the socket library
import os
import socket
import time
import sys

print('server start')

if len(sys.argv) < 3:
	print('wrong number of arguments')
	sys.stderr.write("wrong number of arguments\n")
	sys.stderr.write("usage:\n")
	sys.stderr.write("1: number of nodes\n")
	sys.stderr.write("2: directory where results will be written into file (time.txt) \n")
	sys.exit(1)


# next create a socket object
s = socket.socket()
#print "Socket successfully created"

# reserve a port on your computer in our 
# case it is 12345 but it can be anything 
port = 49538

# Next bind to the port 
# we have not typed any ip in the ip field 
# instead we have inputted an empty string 
# this makes the server listen to requests  
# coming from other computers on the network 
s.bind(('', port))
#print "socket binded to %s" %(port)

# put the socket into listening mode 
s.listen()
#print "socket is listening"

# a forever loop until we interrupt it or  
# an error occurs 
counter = 0
expected_connections = int(sys.argv[1])
# timeFilePath =  os.getcwd() + '/../time.txt'
timeFilePath = sys.argv[2] + 'time.txt'
while True:
# Establish connection with client.
	c, addr = s.accept()
	if counter == 0:
		# start clock
		t0 = time.time()
		print(str(counter) + ',' + str(0), file=open(timeFilePath, 'w'))
	else:
		t1 = time.time()
		print(str(counter) + ',' + str(t1-t0), file=open(timeFilePath, 'a'))
	counter = counter + 1
	if counter == expected_connections:
		break

	# Close the connection with the client
	c.close()

exit(0)
