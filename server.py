# first of all import the socket library 
import socket                
  
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
while True: 
  
# Establish connection with client. 
	c, addr = s.accept()      
	#print 'Got connection from', addr 
	  
	# send a thank you message to the client.  
	#c.send('Thank you for connecting') 
	#print(addr, file=open("C:\\project\\test\\fileName.txt","a"))
	counter = counter + 1
	if counter > 2:
		break


	# Close the connection with the client 
	c.close() 