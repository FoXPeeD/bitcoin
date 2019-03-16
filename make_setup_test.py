#!/usr/local/bin/python

import os, sys
import shutil
import subprocess
import shlex
import time

# parameters
num_clients = 3
utxo_size = 20
debug = 1

# constants
TX_DEFAULT_SENT_AMOUNT = 0.0001
TX_NUMBER_MAX_IN_BLOCK = 10
BASE_PORT_NUM = 18100
BASE_RPC_PORT_NUM = 9100
LOCAL_HOST = '127.0.0.1'


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

def debugPrintNNewLine(string):
	if debug == 1:
		print(string, end='', flush=True)

confDefault = [
	'regtest=1',
	'rpcuser=rpc',
	'rpcpassword=rpc',
	'server=1',
	'listen=1',
	'dbcache=50',
	'whitelist=127.0.0.1',
	'node_dir_placeholder',
	'blocknotify=python3.7 ' + parentDirPath + 'block.py %s'
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


####### create starting blockchain
# print('creating starting block')
# # create directory
# os.chdir(nodesPath)
# if 'starting_chain_node' in os.listdir():
# 	shutil.rmtree('starting_chain_node')
# os.mkdir('starting_chain_node')

# create and make conf file
# os.chdir(binPath)
# node = -1
# confThisNode = confDefault.copy()
# confThisNodeRegTest = confRegtest.copy()
# nodeDir = nodesPath + "starting_chain_node"
# confThisNode[7] = 'datadir=' + nodeDir
# confThisNode[8] = 'loadblock=' + nodeDir + 'regtest/blocks/blk00000.dat'
# port = BASE_PORT_NUM + node
# confThisNodeRegTest[0] = 'port=' + str(port)
# rpcport = BASE_RPC_PORT_NUM + node
# confThisNodeRegTest[1] = 'rpcport=' + str(rpcport)
# confFilePath = nodeDir + delim + "bitcoin.conf"
# contentDefault = '\n'.join(confThisNode)
# contentRegTest = '\n'.join(confThisNodeRegTest)
# with open(confFilePath, "w") as text_file:
# 	text_file.write(contentDefault)
# 	text_file.write('\n\n[regtest]\n')
# 	text_file.write(contentRegTest)

#run bitcoind
# bitcoindCmdArgs[1] = '-conf=' + confFilePath
# btcStartingChain = subprocess.Popen(bitcoindCmdArgs, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
# debugPrint("	started bitcoind of starting chain node")
#
# debugPrint("	waiting for client to finish setup...")
# time.sleep(5)
# initCmdArgs = cliCmdArgs.copy()
# initCmdArgs[3] = '-rpcport=' + str(rpcport)









print('running nodes...')
####### run clients
os.chdir(binPath)
btcClients = []
for node in range(0, num_clients):
	nodeDir = nodesPath + "node" + str(node)
	confDefault[7] = 'datadir=' + nodeDir
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
	debugPrint("	started bitcoind, pid: " + str(btcClients[node].pid))
time.sleep(5)

print('setting up miner node...' )
initCmdArgs = cliCmdArgs.copy()
initCmdArgs[3] = '-rpcport=' + str(BASE_RPC_PORT_NUM + 0) # node 0 will be the miner

# generate blocks for funds
genInitCmdArgs = initCmdArgs.copy()
genInitCmdArgs.append('generate')
genInitCmdArgs.append('101')
genInitRet = subprocess.run(genInitCmdArgs, capture_output=True)
exitWithMessageIfError(genInitRet.stderr, btcClients, 'Error getting address')
debugPrint("	generated 101 Initial blocks")

# get address for Txs
GetAddressCmdArgs = initCmdArgs.copy()
GetAddressCmdArgs.append('getnewaddress')
getAddrRet = subprocess.run(GetAddressCmdArgs, capture_output=True)
exitWithMessageIfError(getAddrRet.stderr, btcClients, 'Error getting address')
addressStr = getAddrRet.stdout.decode("utf-8").split()[0]
debugPrint("	got address " + addressStr)

t0 = time.time()
# send Txs
TxCmdArgs = initCmdArgs.copy()
TxCmdArgs.append('sendtoaddress')
TxCmdArgs.append(addressStr)
TxCmdArgs.append('amount_placeholder') # amount
genInitCmdArgs[5] = '1' # change command's number of generated blocks to 1

for txNum in range(0, utxo_size):
	TxCmdArgs[len(TxCmdArgs)-1] = str(TX_DEFAULT_SENT_AMOUNT)
	sendTxRet = subprocess.run(TxCmdArgs, capture_output=True)
	exitWithMessageIfError(sendTxRet.stderr, btcClients, "Error sending Txs, failed on tx number " + str(txNum))
	debugPrintNNewLine('.')
	if ((txNum+1) % 100) == 0:
		debugPrint('')
		debugPrint('sent 100 Txs')
	if ((txNum+1) % TX_NUMBER_MAX_IN_BLOCK) == 0 and txNum != 0:
		genRet = subprocess.run(genInitCmdArgs, capture_output=True)
		exitWithMessageIfError(genRet.stderr, btcClients, "Error generating block number " + str(txNum / TX_NUMBER_MAX_IN_BLOCK))
genLastRet = subprocess.run(genInitCmdArgs, capture_output=True)
exitWithMessageIfError(genLastRet.stderr, btcClients, "Error generating last block, number:" + str(txNum / TX_NUMBER_MAX_IN_BLOCK))
bestBlockHashMiner = genLastRet.stdout.decode("utf-8").split()[1] # best block hash of miner node
debugPrint('')
debugPrint("	sent all Txs")
timeTook = time.time() - t0
print(str(utxo_size) + ' Txs took ' + str(timeTook) + ' (avg '  + str(timeTook/utxo_size) + ' sec per Tx)')
print('finished generating initial chain')

# make sure all node are synced getbestblockhash
bestBlockCmdArgs = initCmdArgs.copy()
bestBlockCmdArgs.append('getbestblockhash')
allSynced = False
while not allSynced:
	allSynced = True
	for node in range(1, num_clients):
		rpcport = BASE_RPC_PORT_NUM + node
		bestBlockCmdArgs[3] = '-rpcport=' + str(rpcport)
		bestBlockRet = subprocess.run(bestBlockCmdArgs, capture_output=True)
		exitWithMessageIfError(bestBlockRet.stderr, btcClients, 'Error getting address')
		bestBlockHashThisNode = '"' + bestBlockRet.stdout.decode("utf-8").split()[0] + '"'
		if bestBlockHashThisNode != bestBlockHashMiner:
			allSynced = False
			time.sleep(0.5) # wait a bit and start over
			break
debugPrint("	all node are synced")


# start script for timing
serverProc = subprocess.Popen(['python3.7', parentDirPath + 'server.py', str(num_clients)], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
startTime = time.time()


# generate block for timing
generateCmdArgs = cliCmdArgs.copy()
generateCmdArgs.append('generate')  # cmd
generateCmdArgs.append('1')  # amount
generateRet = subprocess.run(genInitCmdArgs, capture_output=True)
exitWithMessageIfError(generateRet.stderr, btcClients, 'Error generating block for timing')
print('generated block for timing')

# wait until server is done timing (all nodes got block)
while serverProc.poll() is None:
	if (time.time() - startTime) > 15:	#
		print('server took too much time to finish')
		for node in range(0,num_clients):
			btcClients[node].terminate()
			serverProc.terminate()
		exit(0)
	else:
		time.sleep(0.5)

print('server finished')
# printProcessOutput(serverProc)
with open(parentDirPath + 'time.txt') as f:
	timeGot= f.read()
	debugPrint('times:\n' + str(timeGot))


input("Press Enter to terminate")
for node in range(0,num_clients):
	btcClients[node].terminate()
print("terminated")


