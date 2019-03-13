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
expected_connection = 2
while True: 
  
# Establish connection with client. 
	c, addr = s.accept()      
	if counter == 0:
		# start clock

	#print(addr, file=open("C:\\project\\test\\fileName.txt","a"))
	counter = counter + 1
	if counter == expected_connection:
		# stop clock
		break


	# Close the connection with the client 
	c.close() 

# print result to file
# return success
