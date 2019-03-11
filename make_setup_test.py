#!/usr/local/bin/python

import os, sys
import shutil
import subprocess
import shlex
import time

NUM_CLIENTS = 2
BASE_PORT_NUM = 18100
BASE_RPC_PORT_NUM = 9100

if sys.platform == "win32":
	#  windows	 ##
	nodesPath = 'C:\\project\\nodes\\'
	binPath = 'C:\\Program Files\\Bitcoin\\daemon'
	parentDirPath = 'C:\\project\\'
	delim = '\\'
	bitcoindFileName = 'bitcoind.exe'
	bitcoin_cliFileName = 'bitcoin-cli.exe'
elif sys.platform == "linux":
	#  linux  ##
	parentDirPath = '/home/blkchprj/bitcoin-git/'
	nodesPath = parentDirPath + 'nodes/'
	binPath = parentDirPath + 'bitcoin/src/'
	delim = '/'
	bitcoindFileName = './bitcoind'
	bitcoin_cliFileName = './bitcoin-cli'
else:
	sys.exit("not supported")

local_host = '127.0.0.1'

confDefault = [
	'rpcuser=rpc',
	'rpcpassword=rpc',
	'server=1',
	'listen=1',
	'dbcache=50',
	'whitelist=127.0.0.1'
]

ConfRegtest = []


bitcoindCmdArgs = [
	bitcoindFileName,
	'node_dir_placeholder',
	'port_placeholder',
	'rpc_port_placeholder',
	'conf_file_placeholder'
	]

cliCmdArgs = [
	bitcoin_cliFileName,
	'-rpcuser=rpc',
	'-rpcpassword=rpc',
	'rpc_port_placeholder'
	]

addNodes = [
	bitcoin_cliFileName,
	'-rpcuser=rpc',
	'-rpcpassword=rpc',
	'-rpc_port_placeholder',
	'connection_placeholder',
	'ip_port_placeholder',
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


time.sleep(5)

####### run clients
os.chdir(binPath)
bc = []
for node in range(0, NUM_CLIENTS):
	nodeDir = nodesPath + "node" + str(node)
	bitcoindCmdArgs[1] = '-datadir=' + nodeDir
	port = BASE_PORT_NUM + node
	bitcoindCmdArgs[2] = '-port=' + str(port)
	rpcport = BASE_RPC_PORT_NUM + node
	bitcoindCmdArgs[3] = '-rpcport=' + str(rpcport)
	confFilePath = nodeDir + delim + "bitcoin.conf"
	bitcoindCmdArgs[4] = '-conf=' + confFilePath
	confThisNode = confDefault.copy()
	for toNode in range(0, NUM_CLIENTS):
		if toNode == node:
			continue
		confThisNode.append('connect=' + local_host + ':' + str(BASE_PORT_NUM + toNode))
	content = '\n'.join(confThisNode)
	print(content)
	with open(confFilePath, "w") as text_file:
		text_file.write(content)

	bc.append(subprocess.Popen(bitcoindCmdArgs, stdout=subprocess.PIPE))
	print("started bitcoind")
	print("pid of client is " + str(bc[node].pid))
	print('')
	time.sleep(5)

# time.sleep(5)

# for i in range(0, NUM_CLIENTS):
# 	addNodes[4] = '-rpcport=' + str(BASE_RPC_PORT_NUM + i)
# 	for j in range(0, NUM_CLIENTS):
# 		if i == j:
# 			continue
# 		addNodes[4] = 'addnode'
# 		addNodes[5] = '"' + local_host + ':' + str(BASE_PORT_NUM + j) + '"'
# 		# print('node ' + str(i) + ': ' + addNodes[5] + ' ' + addNodes[6] + ' ' + addNodes[7])
# 		# addNodes[4] = 'addnode ' + '"' + local_host + ':' + str(BASE_PORT_NUM + j) + '"' + ' add'
# 		addRet = subprocess.run(addNodes, capture_output=True)
# 		addRet = subprocess.run(addNodes, capture_output=True)
# 		addRet = subprocess.run(addNodes, capture_output=True)
# 		# print(addRet.stdout.decode("utf-8"))
# 		# print(" ")
# 		# print(addRet.stderr.decode("utf-8"))
# 		# print('cmd')

generateCmdArgs = cliCmdArgs.copy()
generateCmdArgs.append('')  # cmd
generateCmdArgs.append('')  # amount
generateCmdArgs[4] = 'generate'
generateCmdArgs[5] = '1'
for node in range(0, NUM_CLIENTS):
	if node != 0 :
		continue
	rpcport = BASE_RPC_PORT_NUM + node
	generateCmdArgs[3] = '-rpcport=' + str(rpcport)
	genInitRet = subprocess.run(generateCmdArgs, capture_output=True)
	time.sleep(1)
	print(genInitRet.stdout.decode("utf-8"))
	print(" ")
	print(genInitRet.stderr.decode("utf-8"))
	print('cmd generate')
	print(generateCmdArgs)



input("Press Enter to terminate")
for node in range(0,NUM_CLIENTS):
	bc[node].terminate()
print("terminated")

# out, err = bc[0].communicate()
# print(out.decode("utf-8"))
# if err is not None:
# 	print(err.decode("utf-8"))
