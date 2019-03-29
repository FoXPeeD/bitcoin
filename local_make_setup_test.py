#!/usr/local/bin/python

import os, sys
import shutil
import subprocess
import shlex
import time
import math

# constants
DEFAULT_DB_CHACHE_SIZE_MB = 1.8
TX_DEFAULT_SENT_AMOUNT = 0.0001
BASE_PORT_NUM = 18100
BASE_RPC_PORT_NUM = 9100
LOCAL_HOST = '127.0.0.1'
TYPICAL_TX_SIZE_BYTES = 244
TYPICAL_UTXO_SIZE_BYTES = 77
BYTES_IN_MB = 1000000

if len(sys.argv) < 4:
	print('wrong number of arguments')
	sys.stderr.write("wrong number of arguments\n")
	sys.stderr.write("usage:\n")
	sys.stderr.write("1: block size in MB\n")
	sys.stderr.write("2: percentage of utxo size from dbcache\n")
	sys.stderr.write("3: number of clients\n")
	sys.exit(1)



# parameters
# num_clients = 3
num_clients = int((sys.argv[3]))
# block_size_MB = 0.025
block_size_MB = float(sys.argv[1])
debug = 1
# utxo_size_of_db_cache_size_percentage = 0.1
utxo_size_of_db_cache_size_percentage = float(sys.argv[2])

delim = '/'
parentDirPath = os.getcwd() + '/'
nodesPath = parentDirPath + '../nodes/'
binPath = parentDirPath + 'src/'
bitcoindFileName = './bitcoind'
bitcoin_cliFileName = './bitcoin-cli'


####### helper functions
def printByteStreamOut(stream, processName=''):
	print('# ' + processName + ' stdout:')
	if stream is None:
		print('<Empty>')
	else:
		print(stream.decode("utf-8"))
	print('')


def printByteStreamErr(stream, processName=''):
	print('$ ' + processName + ' stderr:')
	if stream is None:
		print('<Empty>')
	else:
		print(stream.decode("utf-8"))
	print('')


def printProcessOutput(proc):
	out, err = proc.communicate()
	printByteStreamOut(out, 'd')
	printByteStreamErr(err, 'd')


def errorReturned(stream):
	if stream is None:
		return False
	errStrListSet = set(stream.decode("utf-8").split('\n'))
	if '' in errStrListSet and len(errStrListSet) == 1:
		return False
	else:
		return True


def exitWithMessageIfError(stream, process, errString):
	if errorReturned(stream):
		print('Error received:')
		print(stream.decode("utf-8"))
		if process is not None:
			if isinstance(process, list):
				for proc in process:
					proc.terminate()
			else:
				process.terminate()
		sys.exit(errString)


def debugPrint(string):
	if debug == 1:
		print(string)

def debugPrintNewLine(string):
	if debug == 1:
		print(string, end='', flush=True)

confDefault = [
	'regtest=1',
	'rpcuser=rpc',
	'rpcpassword=rpc',
	'server=1',
	'listen=1',
	'dbcache=4',  # actual UTXO set allocated on memory is 1.8MB (for 4MB dbcache)
	'whitelist=127.0.0.1',
	'node_dir_placeholder',
	'blocknotify=' + parentDirPath + 'local_block.py %s',
	'blocksonly=0'  # ,
	# 'maxmempool=4'
]

confRegtest = [
	'port_placeholder',
	'rpc_port_placeholder'
	]


bitcoindCmdArgs = [
	bitcoindFileName,
	'conf_file_placeholder'
	]

cliCmdArgs = [
	bitcoin_cliFileName,
	'-rpcuser=rpc',
	'-rpcpassword=rpc',
	'rpc_port_placeholder'
	]


####### clean data directories of nodes
os.chdir(parentDirPath+'../')
if 'nodes' in os.listdir():
	shutil.rmtree('nodes')
os.mkdir(nodesPath)


####### create data directories of nodes
os.chdir(nodesPath)
for node in range(0, num_clients):
	os.mkdir('node' + str(node))
	os.mkdir('node' + str(node) + '/blocks/')

####### make data dir if not found
os.chdir(parentDirPath+'../')
if 'data_dirs' not in os.listdir():
	os.mkdir('data_dirs')
os.chdir(nodesPath + '/../data_dirs/')
utxo_size_MB = DEFAULT_DB_CHACHE_SIZE_MB * (utxo_size_of_db_cache_size_percentage / 100)
utxo_set_size = math.floor((utxo_size_MB * BYTES_IN_MB) / TYPICAL_UTXO_SIZE_BYTES)
print('utxo set size is ' + str(utxo_set_size))
print('utxo set size in MB is ' + str(utxo_size_MB))

MAX_TX_IN_BLOCK = math.floor((block_size_MB * BYTES_IN_MB) / TYPICAL_TX_SIZE_BYTES)
print('Txs in block is ' + str(MAX_TX_IN_BLOCK))
print('block size in MB is ' + str(block_size_MB))

dataDir = 'utxo-size-MB=' + str(utxo_size_MB) + '_block-size-MB=' + str(block_size_MB)
if dataDir not in os.listdir():
	makeDirCmdArgs = [
		'python3.7',
		'create_starting_blockchain.py',
		str(block_size_MB),
		str(utxo_size_of_db_cache_size_percentage)
	]
	os.chdir(parentDirPath)
	print('running create_starting_blockchain.py script')
	makeDirRes = subprocess.run(makeDirCmdArgs, capture_output=False)
	exitWithMessageIfError(makeDirRes.stderr, None, 'Error making data dir')


####### move data to directories of nodes
os.chdir(nodesPath)
for node in range(0, num_clients):
	nodeDir = nodesPath + "node" + str(node)
	cpCmdArgs = [
		'cp',
		'-rf',
		nodeDir + '/../../data_dirs/' + 'utxo-size-MB=' + str(utxo_size_MB) + '_block-size-MB=' + str(block_size_MB) + '/regtest/',
		nodeDir + '/regtest/'
	]
	cpRes=subprocess.run(cpCmdArgs, capture_output=True)
	exitWithMessageIfError(cpRes.stderr, None, 'Error moving dirs')

####### remove sent Tx data from non-miner nodes
os.chdir(nodesPath)
for node in range(1, num_clients):
	nodeDir = nodesPath + "node" + str(node)
	rmCmdArgs = [
		'rm',
		nodeDir + '/regtest/mempool.dat'
	]
	rmRes = subprocess.run(rmCmdArgs, capture_output=True)
	exitWithMessageIfError(rmRes.stderr, None, 'Error removing mempool.dat')

print('running nodes...')
# make conf files and start clients
os.chdir(binPath)
btcClients = []
for node in range(0, num_clients):
	nodeDir = nodesPath + "node" + str(node)
	confDefault[7] = 'datadir=' + nodeDir
	if node == 0:
		confDefault[9] = 'blocksonly=0'
		# confDefault[10] = 'maxmempool=32'
	else:
		confDefault[9] = 'blocksonly=1'
		# confDefault[10] = 'maxmempool=4'
	port = BASE_PORT_NUM + node
	confRegtest[0] = 'port=' + str(port)
	rpcport = BASE_RPC_PORT_NUM + node
	confRegtest[1] = 'rpcport=' + str(rpcport)
	confFilePath = nodeDir + delim + "bitcoin.conf"
	bitcoindCmdArgs[1] = '-conf=' + confFilePath
	confThisNode = confDefault.copy()
	confThisNodeRegTest = confRegtest.copy()
	for toNode in range(0, num_clients):
		if toNode == node:
			continue
		confThisNodeRegTest.append('connect=' + LOCAL_HOST + ':' + str(BASE_PORT_NUM + toNode))
	content = '\n'.join(confThisNode)
	contentRegTest = '\n'.join(confThisNodeRegTest)
	with open(confFilePath, "w") as text_file:
		text_file.write(content)
		text_file.write('\n\n[regtest]\n')
		text_file.write(contentRegTest)
	btcClients.append(subprocess.Popen(bitcoindCmdArgs, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT))
	# print(bitcoindCmdArgs)
	debugPrint("	started bitcoind, pid: " + str(btcClients[node].pid))
time.sleep(15)

input('press enter to start timing')

print('setting up miner node...' )
initCmdArgs = cliCmdArgs.copy()
initCmdArgs[3] = '-rpcport=' + str(BASE_RPC_PORT_NUM) # node 0 will be the miner

# make sure all node are synced getbestblockhash
bestBlockCmdArgs = initCmdArgs.copy()
bestBlockCmdArgs.append('getbestblockhash')
node = 0
rpcport = BASE_RPC_PORT_NUM + node
bestBlockCmdArgs[3] = '-rpcport=' + str(rpcport)
bestBlockRet = subprocess.run(bestBlockCmdArgs, capture_output=True)
exitWithMessageIfError(bestBlockRet.stderr, btcClients, 'Error getting miner node best block hash')
bestBlockHashMinerNode = '"' + bestBlockRet.stdout.decode("utf-8").split()[0] + '"'

for node in range(1, num_clients):
	rpcport = BASE_RPC_PORT_NUM + node
	bestBlockCmdArgs[3] = '-rpcport=' + str(rpcport)
	bestBlockRet = subprocess.run(bestBlockCmdArgs, capture_output=True)
	exitWithMessageIfError(bestBlockRet.stderr, btcClients, 'Error getting node best block hash')
	bestBlockHashThisNode = '"' + bestBlockRet.stdout.decode("utf-8").split()[0] + '"'
	if bestBlockHashThisNode != bestBlockHashMinerNode:
		for process in btcClients:
				process.terminate()
		sys.exit("nodes' blockchain are not synced")
debugPrint("	all node are synced")


# start script for timing
serverCmdArgs = [
	'python3.7',
	parentDirPath + 'server.py',
	str(num_clients),
	parentDirPath + '../'
]
print(parentDirPath + '../')
serverProc = subprocess.Popen(serverCmdArgs, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
startTime = time.time()

input('press enter to generate')
# generate block for timing
generateCmdArgs = cliCmdArgs.copy()
rpcport = BASE_RPC_PORT_NUM + 0
generateCmdArgs[3] = '-rpcport=' + str(rpcport)
generateCmdArgs.append('generate')  # cmd
generateCmdArgs.append('1')  # amount
generateRet = subprocess.run(generateCmdArgs, capture_output=True)
exitWithMessageIfError(generateRet.stderr, btcClients, 'Error generating block for timing')
print('generated block for timing')

# wait until server is done timing (all nodes got block)
while serverProc.poll() is None:
	if (time.time() - startTime) > 30:
		print('server took too much time to finish')
		for node in range(0, num_clients):
			btcClients[node].terminate()
			serverProc.terminate()
		exit(0)
	else:
		time.sleep(0.5)

print('server finished')
# printProcessOutput(serverProc)
with open(parentDirPath + '../time.txt') as f:
	timeGot = f.read()
	debugPrint('times:\n' + str(timeGot))


input("Press Enter to terminate")
for node in range(0, num_clients):
	btcClients[node].terminate()
print("terminated")


