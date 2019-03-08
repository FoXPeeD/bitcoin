#!/usr/bin/python

import os, sys
import shutil
import subprocess
import shlex
import time


NUM_TX = 1
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
	'-rpcport=' + str(BASE_RPC_PORT_NUM - 1),
	''

	]

# clean and recreate dir
os.chdir(parentDirPath)
if 'nodes' not in os.listdir():
	os.mkdir(nodesPath)
os.chdir(nodesPath)
if 'starting_chain_node' in os.listdir():
	shutil.rmtree('starting_chain_node')
os.mkdir('starting_chain_node')

# start bitcoind
os.chdir(binPath)
nodeDir = nodesPath + "starting_chain_node"
bitcoindCmdArgs[2] = '-datadir=' + nodeDir
port = BASE_PORT_NUM - 1
bitcoindCmdArgs[3] = '-port=' + str(port)
rpcport = BASE_RPC_PORT_NUM - 1
bitcoindCmdArgs[4] = '-rpcport=' + str(rpcport)
confFilePath = nodeDir + delim + "bitcoin.conf"
with open(confFilePath, "w") as text_file:
	print(f'rpcuser=rpc\nrpcpassword=rpc\nserver=1\nlisten=1\ndbcache=50', file=text_file)
bitcoind = subprocess.Popen(bitcoindCmdArgs, stdout=subprocess.PIPE)
print("bitcoind started")
time.sleep(5)

# get address for Txs
GetAddressCmdArgs = cliCmdArgs
GetAddressCmdArgs[5] = 'getnewaddress'

ret = subprocess.run(cliCmdArgs, capture_output=True)
print("ret output:")
print(ret.stdout)
print("ret error:")
print(ret.stderr)
# if ret != 0:
# 	sys.exit("Error getting address")

out, err = bitcoind.communicate()
print("d output:")
print(out.decode("utf-8"))
print("d error:")
print(err.decode("utf-8"))
bitcoind.terminate()
#
# TxCmdArgs = cliCmdArgs
# for txNum in range(0, NUM_TX):
#
# 	ret = subprocess.call(cliCmdArgs, stdout=subprocess.PIPE)
# 	if ret != 0:
# 		sys.exit("Error sending Txs")
#

