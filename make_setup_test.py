#!/usr/local/bin/python

import os, sys
import shutil
import subprocess
import shlex
import time

NUM_CLIENTS = 2
BASE_PORT_NUM = 18100
BASE_RPC_PORT_NUM = 9100

##  windows	 ##
nodesPath = 'C:\\project\\nodes\\'
binPath = 'C:\\Program Files\\Bitcoin\\daemon'
parentDirPath = 'C:\\project\\'
delim = '\\'
bitcoindFileName = 'bitcoind.exe'
bitcoin_cliFileName = 'bitcoin-cli.exe'

##  linux  ##
#parentDirPath = '/home/blkchprj/bitcoin-git/'
#nodesPath = parentDirPath + 'nodes/'
#binPath = parentDirPath + 'bitcoin/src/'
#delim = '/'
#bitcoindFileName = './bitcoind'
#bitcoin_cliFileName = './bitcoin-cli'

local_host = '127.0.0.1'

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

addNodes = [
	bitcoin_cliFileName,
	'-regtest',
	'-rpcuser=rpc',
	'-rpcpassword=rpc',
	'-rpc_port_placeholder',
	'connection_placeholder',
	'add'
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
		print(f'rpcuser=rpc\nrpcpassword=rpc\nserver=1\nlisten=1\ndbcache=50', file=text_file)

	bc.append(subprocess.Popen(bitcoindCmdArgs, stdout=subprocess.PIPE))
	print("started bitcoind")
	print("pid of client is " + str(bc[node].pid))

# time.sleep(5)

for i in range(0, NUM_CLIENTS):
	addNodes[4] = '-rpcport=' + str(BASE_PORT_NUM + i)
	for j in range(0, NUM_CLIENTS):
		if i == j:
			continue
		addNodes[5] = 'addnode "' + local_host + ':' + str(BASE_PORT_NUM + j) + '"'
		addRet = subprocess.run(addNodes, capture_output=True)


input("Press Enter to terminate")
for node in range(0,NUM_CLIENTS):
	bc[node].terminate()
print("terminated")
