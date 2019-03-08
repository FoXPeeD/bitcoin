#!/usr/bin/python

import os, sys
import shutil
import subprocess
import shlex
import time


NUM_TX = 1
TX_DEFAULT_SENT_AMOUNT = 0.0001
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
	errStrListSet = set(stream.decode("utf-8").split('\n'))
	if '' in errStrListSet and len(errStrListSet) == 1:
		return False
	else:
		return True

def exitWithMessageIfError(stream, errString):
	if errorReturned(stream):
		print('Error received:')
		print(stream.decode("utf-8"))
		bitcoind.terminate()
		sys.exit(errString)


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
GetAddressCmdArgs = cliCmdArgs.copy()
GetAddressCmdArgs[5] = 'getnewaddress'
getAddrRet = subprocess.run(GetAddressCmdArgs, capture_output=True)
addressStr = getAddrRet.stdout.decode("utf-8").split()[0]
if len(addressStr) > 35 or len(addressStr) < 26:
	printByteStreamOut(getAddrRet.stdout, 'cli')
	printByteStreamErr(getAddrRet.stderr, 'cli')
	bitcoind.terminate()
	printProcessOutput(bitcoind)
	sys.exit('Error getting address')


# generate blocks for funds
generateCmdArgs = cliCmdArgs.copy()
generateCmdArgs.append('')  # amount
generateCmdArgs[5] = 'generate'
generateCmdArgs[6] = '101'
genRet = subprocess.run(generateCmdArgs, capture_output=True)
# printByteStreamOut(genRet.stdout, 'cli')
# printByteStreamErr(genRet.stderr, 'cli')
exitWithMessageIfError(genRet.stderr, "Error generating initial blocks")


# send Txs
TxCmdArgs = cliCmdArgs.copy()
TxCmdArgs.append('')  # address
TxCmdArgs.append('')  # amount
TxCmdArgs[5] = 'sendtoaddress'
TxCmdArgs[6] = addressStr
for txNum in range(0, NUM_TX):
	TxCmdArgs[7] = str(TX_DEFAULT_SENT_AMOUNT)
	sendTxRet = subprocess.run(TxCmdArgs, capture_output=True)
	# printByteStreamOut(sendTxRet.stdout, 'cli')
	# printByteStreamErr(sendTxRet.stderr, 'cli')
	if errorReturned(sendTxRet.stderr):
		bitcoind.terminate()
		sys.exit("Error sending Txs")

bitcoind.terminate()
# printProcessOutput(bitcoind)
