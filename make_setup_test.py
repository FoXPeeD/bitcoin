#!/usr/bin/python

import os, sys
import shutil
import subprocess
import shlex
import time

NUM_CLIENTS = 4
BASE_PORT_NUM = 18100
BASE_RPC_PORT_NUM = 9100

##  windows	 ##
# nodesPath = 'C:\\Technion\\project2\\nodes\\'
# binPath = 'C:\\Technion\\project2\\bitcoin-0.17.0\\bin'
# paretDirPath = 'C:\\Technion\\project2\\'
# delim = '\\'
# bitcoindFileName = './bitcoind.exe'
# bitcoin_cliFileName = './bitcoin-cli.exe'

##  linux  ##
parentDirPath = '/home/blkchprj/bitcoin-git/'
nodesPath = parentDirPath + 'nodes/'
binPath = parentDirPath + 'bitcoin/src/'
delim = '/'
bitcoindFileName = './bitcoind'
bitcoin_cliFileName = './bitcoin-cli'

bitcoindCmdArgs = [
	bitcoindFileName,
	'-regtest',
	'node_dir_placeholder',
	'port_placeholder',
	'rpc_port_placeholder'
	]

cliCmdArgs = [
	bitcoin_cliFileName,
	'-regtest',
	'-rpcuser=rpc',
	'-rpcpassword=rpc',
	'-rpcport=9101'
	]

####### setup nodes
os.chdir(parentDirPath)
if 'nodes' in os.listdir():
	shutil.rmtree('nodes')
os.mkdir(nodesPath)
os.chdir(nodesPath)
for node in range(0, NUM_CLIENTS):
	os.mkdir('node' + str(node))
#	TODO: copy files from start blockchain node

####### run clients
os.chdir(binPath)
bc = []
for node in range(0, NUM_CLIENTS):
	nodeDir = nodesPath + "node" + str(node)
	bitcoindCmdArgs[2] = '-datadir=' + nodeDir
	port = BASE_PORT_NUM + node
	bitcoindCmdArgs[3] = '-port=' + str(port)
	rpcport = BASE_RPC_PORT_NUM + node
	bitcoindCmdArgs[4] = '-rpcport=' + str(rpcport)
	confFilePath = nodeDir + delim + "bitcoin.conf"
	with open(confFilePath, "w") as text_file:
		print(f'rpcuser=rpc\nrpcpassword=rpc\nserver=1\nlisten=1\nrpcallowip=0.0.0.0\n-dbcache=50', file=text_file)

	bc.append(subprocess.Popen(bitcoindCmdArgs, stdout=subprocess.PIPE))
	print("started bitcoind")
	print("pid of client is " + str(bc[node].pid))

input("Press Enter to terminate")
for node in range(0,NUM_CLIENTS):
	bc[node].terminate()
print("terminated")
