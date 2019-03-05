#!/usr/bin/python

import os, sys
import shutil
import subprocess
import shlex
import time


args = [
	'./bitcoind.exe',
	'-regtest',
	'node_dir_placeholder',
	'port_placeholder',
	'rpc_port_placeholder'
	]

path = 'C:\\Technion\\project2\\nodes\\'
binPath = 'C:\\Technion\\project2\\bitcoin-0.17.0\\bin'
NUM_CLIENTS=2
os.chdir('C:\\Technion\\project2\\');
if 'nodes' in os.listdir():
	shutil.rmtree('nodes')
os.mkdir(path);
os.chdir(path);
for node in range(0,NUM_CLIENTS):
	os.mkdir( 'node' + str(node) );

os.chdir(binPath);
bc = []
for node in range(0,NUM_CLIENTS):
	
	
	with open("..\\..\\nodes\\node" + str(node) + "\\bitcoin.conf", "w") as text_file:
		print(f"rpcuser=rpc\nrpcpassword=rpc\nserver=1\nlisten=1", file=text_file)
		# print(f"rpcuser=rpc\nrpcpassword=rpc\nserver=1\nport={port}\nrpcport={rpcport}", file=text_file)
		# print(f"Purchase Amount: {TotalAmount}", file=text_file)
	nodeDir = "C:\\Technion\\project2\\nodes\\node" + str(node)
	args[2] = '-datadir=' + nodeDir;
	port = 18100 + node;
	args[3] = '-port=' + str(port);
	rpcport = 9100 + node;
	args[4] = '-rpcport=' + str(rpcport);

	bc.append(subprocess.Popen(args,stdout=subprocess.PIPE))
	print ("started bitcoind");
	print ("pid of client is " + str(bc[node].pid) );
	
input("Press Enter to terminate")
for node in range(0,NUM_CLIENTS):
	bc[node].terminate();
print ("terminated");
	