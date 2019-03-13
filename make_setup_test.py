#!/usr/local/bin/python

import os, sys
import shutil
import subprocess
import shlex
import time

# parameters
num_clients = 5
utxo_size = 500
debug = 1

# constants
TX_DEFAULT_SENT_AMOUNT = 0.0001
TX_NUMBER_MAX_IN_BLOCK = 5
BASE_PORT_NUM = 18100
BASE_RPC_PORT_NUM = 9100
LOCAL_HOST = '127.0.0.1'

if sys.platform == "win32":
	#  windows	 ##
	delim = '\\'
	parentDirPath = 'C:\\project\\'
	nodesPath = parentDirPath + 'nodes\\'
	binPath = 'C:\\Program Files\\Bitcoin\\daemon'
	bitcoindFileName = 'bitcoind.exe'
	bitcoin_cliFileName = 'bitcoin-cli.exe'
elif sys.platform == "linux":
	#  linux  ##
	delim = '/'
	parentDirPath = os.getcwd() + '/'
	nodesPath = parentDirPath + '../nodes/'
	binPath = parentDirPath + 'src/'
	bitcoindFileName = './bitcoind'
	bitcoin_cliFileName = './bitcoin-cli'
else:
	sys.exit("not supported")

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
			process.terminate()
		sys.exit(errString)


def debugPrint(string):
	if debug == 1:
		print(string)

confDefault = [
	'regtest=1',
	'rpcuser=rpc',
	'rpcpassword=rpc',
	'server=1',
	'listen=1',
	'dbcache=50',
	'whitelist=127.0.0.1',
	'node_dir_placeholder'
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
print('creating starting block')
# create directory
os.chdir(nodesPath)
if 'starting_chain_node' in os.listdir():
	shutil.rmtree('starting_chain_node')
os.mkdir('starting_chain_node')

# create and make conf file
os.chdir(binPath)
node = -1
confThisNode = confDefault.copy()
confThisNodeRegTest = confRegtest.copy()
nodeDir = nodesPath + "starting_chain_node"
confThisNode[7] = 'datadir=' + nodeDir
port = BASE_PORT_NUM + node
confThisNodeRegTest[0] = 'port=' + str(port)
rpcport = BASE_RPC_PORT_NUM + node
confThisNodeRegTest[1] = 'rpcport=' + str(rpcport)
confFilePath = nodeDir + delim + "bitcoin.conf"
contentDefault = '\n'.join(confThisNode)
contentRegTest = '\n'.join(confThisNodeRegTest)
print(confFilePath)
with open(confFilePath, "w") as text_file:
	text_file.write(contentDefault)
	text_file.write('\n\n[regtest]\n')
	text_file.write(contentRegTest)

#run bitcoind
bitcoindCmdArgs[1] = '-conf=' + confFilePath
btcStartingChain = subprocess.Popen(bitcoindCmdArgs, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
debugPrint("	started bitcoind of starting chain node")

debugPrint("	waiting for client to finish setup...")
time.sleep(5)
initCmdArgs = cliCmdArgs.copy()
initCmdArgs[3] = '-rpcport=' + str(rpcport)

# get address for Txs
GetAddressCmdArgs = initCmdArgs.copy()
GetAddressCmdArgs.append('getnewaddress')
getAddrRet = subprocess.run(GetAddressCmdArgs, capture_output=True)
exitWithMessageIfError(getAddrRet.stderr, btcStartingChain, 'Error getting address')
addressStr = getAddrRet.stdout.decode("utf-8").split()[0]
debugPrint("	got address " + addressStr)

# generate blocks for funds
genInitCmdArgs = initCmdArgs.copy()
genInitCmdArgs.append('generate')
genInitCmdArgs.append('101')
genInitRet = subprocess.run(genInitCmdArgs, capture_output=True)
exitWithMessageIfError(genInitRet.stderr, btcStartingChain, 'Error getting address')
debugPrint("	generated Initial blocks (101)")

# send Txs
TxCmdArgs = initCmdArgs.copy()
TxCmdArgs.append('sendtoaddress')
TxCmdArgs.append(addressStr)
TxCmdArgs.append('amount_placeholder') # amount
genInitCmdArgs[5] = '1' # change command's number of generated blocks to 1

for txNum in range(0, utxo_size):
	TxCmdArgs[len(TxCmdArgs)-1] = str(TX_DEFAULT_SENT_AMOUNT)
	sendTxRet = subprocess.run(TxCmdArgs, capture_output=True)
	exitWithMessageIfError(sendTxRet.stderr, btcStartingChain, "Error sending Txs, failed on tx number " + str(txNum))
	if ((txNum+1) % 100) == 0:
		debugPrint('sent 100 Txs')
	if ((txNum+1) % TX_NUMBER_MAX_IN_BLOCK) == 0 and txNum != 0:
		genRet = subprocess.run(genInitCmdArgs, capture_output=True)
		exitWithMessageIfError(genRet.stderr, btcStartingChain, "Error generating block number " + str(txNum / TX_NUMBER_MAX_IN_BLOCK))
genLastRet = subprocess.run(genInitCmdArgs, capture_output=True)
exitWithMessageIfError(genLastRet.stderr, btcStartingChain, "Error generating last block, number:" + str(txNum / TX_NUMBER_MAX_IN_BLOCK))
debugPrint("	sent all Txs")
print('created starting block')


btcStartingChain.terminate()
####### move files to directories of nodes
#	TODO: copy files from start blockchain node


####### run clients
os.chdir(binPath)
bc = []
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

	bc.append(subprocess.Popen(bitcoindCmdArgs, stdout=subprocess.PIPE))
	print("started bitcoind")
	print("pid of client is " + str(bc[node].pid))
	print('')
	time.sleep(5)


# generateCmdArgs = cliCmdArgs.copy()
# generateCmdArgs.append('')  # cmd
# generateCmdArgs.append('')  # amount
# generateCmdArgs[4] = 'generate'
# generateCmdArgs[5] = '1'
# for node in range(0, num_clients):
# 	if node != 0 :
# 		continue
# 	rpcport = BASE_RPC_PORT_NUM + node
# 	generateCmdArgs[3] = '-rpcport=' + str(rpcport)
# 	genInitRet = subprocess.run(generateCmdArgs, capture_output=True)
# 	time.sleep(1)
# 	print(genInitRet.stdout.decode("utf-8"))
# 	print(" ")
# 	print(genInitRet.stderr.decode("utf-8"))
# 	print('cmd generate')
# 	print(generateCmdArgs)



input("Press Enter to terminate")
for node in range(0,num_clients):
	bc[node].terminate()
print("terminated")

# out, err = bc[0].communicate()
# print(out.decode("utf-8"))
# if err is not None:
# 	print(err.decode("utf-8"))

