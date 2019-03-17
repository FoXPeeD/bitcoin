#!/usr/bin/python

import os, sys
import shutil
import subprocess
import shlex
import time
import math

# constants
DEFAULT_DB_CHACHE_SIZE_MB = 4
TX_DEFAULT_SENT_AMOUNT = 0.0001
BASE_PORT_NUM = 18100
BASE_RPC_PORT_NUM = 9100
LOCAL_HOST = '127.0.0.1'
TYPICAL_TX_SIZE_BYTES = 244
TYPICAL_UTXO_SIZE_BYTES = 77
BYTES_IN_MB = 1000000

if len(sys.argv) < 3:
	print('wrong number of arguments')
	sys.stderr.write("wrong number of arguments\n")
	sys.stderr.write("usage:\n")
	sys.stderr.write("1: block size in MB\n")
	sys.stderr.write("2: percentage of utxo size from dbcache\n")
	sys.exit(1)



# parameters
num_clients = 3
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
	'dbcache=50',
	'whitelist=127.0.0.1',
	'node_dir_placeholder',
	'blocknotify=python3.7 ' + parentDirPath + 'block.py %s',
	'maxmempool=32'
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

####### create data directory of node
os.chdir(parentDirPath+'../')
if 'nodes' not in os.listdir():
	os.mkdir(nodesPath)
os.chdir(nodesPath)
if 'node_maker' in os.listdir():
	shutil.rmtree('node_maker')
os.mkdir('node_maker')

utxo_size_MB = DEFAULT_DB_CHACHE_SIZE_MB * (utxo_size_of_db_cache_size_percentage / 100)
utxo_set_size = math.floor((utxo_size_MB * BYTES_IN_MB) / TYPICAL_UTXO_SIZE_BYTES)
print('utxo set size is ' + str(utxo_set_size))
print('utxo set size in MB is ' + str(utxo_size_MB))

MAX_TX_IN_BLOCK = math.floor((block_size_MB * BYTES_IN_MB) / TYPICAL_TX_SIZE_BYTES)
print('Txs in block is ' + str(MAX_TX_IN_BLOCK))
print('block size in MB is ' + str(block_size_MB))


os.chdir(parentDirPath+'../')
if 'data_dirs' not in os.listdir():
	os.mkdir('data_dirs')

# remove old folder if already present
os.chdir(nodesPath)
dataDir = 'utxo-size-MB=' + str(utxo_size_MB) + '_block-size-MB=' + str(block_size_MB)
if dataDir in os.listdir():
	shutil.rmtree(dataDir)




# create and make conf file
os.chdir(binPath)
node = -1
confThisNode = confDefault.copy()
confThisNodeRegTest = confRegtest.copy()
nodeDir = nodesPath + "node_maker"
confThisNode[7] = 'datadir=' + nodeDir
port = BASE_PORT_NUM + node
confThisNodeRegTest[0] = 'port=' + str(port)
rpcport = BASE_RPC_PORT_NUM + node
confThisNodeRegTest[1] = 'rpcport=' + str(rpcport)
confFilePath = nodeDir + delim + "bitcoin.conf"
contentDefault = '\n'.join(confThisNode)
contentRegTest = '\n'.join(confThisNodeRegTest)
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

# generate blocks for funds
genInitCmdArgs = initCmdArgs.copy()
genInitCmdArgs.append('generate')
blksNeeded = 101 + math.ceil((utxo_set_size+MAX_TX_IN_BLOCK)/25) # generate enough balance under the assumption that all Tx will be sent in one block
genInitCmdArgs.append(str(blksNeeded))
genInitRet = subprocess.run(genInitCmdArgs, capture_output=True)
exitWithMessageIfError(genInitRet.stderr, btcStartingChain, 'Error getting address')
debugPrint("	generated " + str(blksNeeded) + " Initial blocks")


## get address for Txs
# GetAddressCmdArgs = initCmdArgs.copy()
# GetAddressCmdArgs.append('getnewaddress')
# getAddrRet = subprocess.run(GetAddressCmdArgs, capture_output=True)
# exitWithMessageIfError(getAddrRet.stderr, btcStartingChain, 'Error getting address')
# addressStr = getAddrRet.stdout.decode("utf-8").split()[0]
# debugPrint("	got address " + addressStr)
addressStr = '2N6gFPhAAUbvnPk7YnUvrQ3pE5FZAwDEb3K' # address not belonging to either nodes



t0 = time.time()
# send Txs for UTXO
TxCmdArgs = initCmdArgs.copy()
TxCmdArgs.append('sendtoaddress')
TxCmdArgs.append(addressStr)
TxCmdArgs.append('amount_placeholder') # amount
genInitCmdArgs[5] = '1' # change command's number of generated blocks to 1

for txNum in range(0, utxo_set_size):
	TxCmdArgs[len(TxCmdArgs)-1] = str(TX_DEFAULT_SENT_AMOUNT)
	sendTxRet = subprocess.run(TxCmdArgs, capture_output=True)
	exitWithMessageIfError(sendTxRet.stderr, btcStartingChain, "Error sending Txs, failed on tx number " + str(txNum))
	# printByteStreamOut(sendTxRet.stdout, 'd') # print Tx hashes
	debugPrintNewLine('.')
	if ((txNum+1) % 100) == 0:
		debugPrint('\nsent 100 Txs')
	if ((txNum+1) % MAX_TX_IN_BLOCK) == 0 and txNum != 0:
		genRet = subprocess.run(genInitCmdArgs, capture_output=True)
		exitWithMessageIfError(genRet.stderr, btcStartingChain, "Error generating block number " + str(txNum / MAX_TX_IN_BLOCK))
		# printByteStreamOut(genRet.stdout, 'd') # print block hash
genLastRet = subprocess.run(genInitCmdArgs, capture_output=True)
exitWithMessageIfError(genLastRet.stderr, btcStartingChain, "Error generating last block, number:" + str(txNum / MAX_TX_IN_BLOCK))
bestBlockHashMiner = genLastRet.stdout.decode("utf-8").split()[1] # best block hash of miner node
debugPrint("\n	sent all Txs")
timeTook = time.time() - t0
debugPrint('\n')
print(str(utxo_set_size) + ' UTXO Txs took ' + str(timeTook) + ' (avg '  + str(timeTook/utxo_set_size) + ' sec per Tx)')
print('finished generating initial chain')


# send Txs without mining
t1 = time.time()
TxCmdArgs = initCmdArgs.copy()
TxCmdArgs.append('sendtoaddress')
TxCmdArgs.append(addressStr)
TxCmdArgs.append('amount_placeholder') # amount

for txNum in range(0, MAX_TX_IN_BLOCK):
	TxCmdArgs[len(TxCmdArgs)-1] = str(TX_DEFAULT_SENT_AMOUNT)
	sendTxRet = subprocess.run(TxCmdArgs, capture_output=True)
	exitWithMessageIfError(sendTxRet.stderr, btcStartingChain, "Error sending Txs, failed on tx number " + str(txNum))
	# printByteStreamOut(sendTxRet.stdout, 'd') # print Tx hashes
	debugPrintNewLine('.')
	if ((txNum+1) % 100) == 0:
		debugPrint('\nsent 100 Txs')
debugPrint("\n	sent all Txs")
timeTook = time.time() - t1
debugPrint('\n')
print(str(utxo_set_size) + ' of waiting Txs took ' + str(timeTook) + ' (avg '  + str(timeTook/utxo_set_size) + ' sec per Tx)')
print('finished generating initial chain')


btcStartingChain.terminate()
time.sleep(1) # give client time to close properly before copying
print("bitcoind terminated")


# copy directory.
cpCmdArgs=[
	'cp',
	'-rf',
	nodeDir,
	nodeDir + '/../../data_dirs/' + 'utxo-size-MB=' + str(utxo_size_MB) + '_block-size-MB=' + str(block_size_MB)

]
ret=subprocess.run(cpCmdArgs, capture_output=True)

