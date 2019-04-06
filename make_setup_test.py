#!/usr/local/bin/python

import sys
import os
import shutil
import subprocess
import shlex
import time
import math
import paramiko
import boto3
import random
from scp import SCPClient
from datetime import datetime
from datetime import timedelta

# constants
DEFAULT_DB_CHACHE_SIZE_MB = 1.8
TX_DEFAULT_SENT_AMOUNT = 0.0001
BASE_PORT_NUM = 18100
BASE_RPC_PORT_NUM = 9100
LOCAL_HOST = '127.0.0.1'
PRIVATE_IP_PREFIX = '10.0.2.1'
TYPICAL_TX_SIZE_BYTES = 245
TYPICAL_UTXO_SIZE_BYTES = 77
BYTES_IN_MB = 1000000
TAR_FILE_FULL_NAME = 'data-full.tar.gz'
TAR_FILE_NO_MEMPOOL_NAME = 'data-no-mempool.tar.gz'
EMPTY_LIST = []
SEED_STR = 'tal_itzik'
NUMBER_OF_CONNECTIONS = 4
CONNECTION_SET = {}
debug = 1  # verbose flag for debugging

if len(sys.argv) < 5:
	print('wrong number of arguments')
	sys.stderr.write("wrong number of arguments\n")
	sys.stderr.write("usage:\n")
	sys.stderr.write("1: block size in MB\n")
	sys.stderr.write("2: percentage of utxo size from dbcache\n")
	sys.stderr.write("3: number of clients\n")
	sys.stderr.write("4: connectivity type of nodes\n")
	sys.exit(1)


delim = '/'
localBaseDirPath = os.getcwd() + '/'
nodesPath = localBaseDirPath + '../nodes/'
localBinPath = localBaseDirPath + 'src/'
bitcoindFileName = './bitcoind'
bitcoin_cliFileName = './bitcoin-cli'
remoteBaseDirPath = '/home/ubuntu/project/'
remoteDataDirPath = remoteBaseDirPath + 'dataDir/'
remoteBinPath = remoteBaseDirPath + 'bitcoin/src/'
KEYFILE = localBaseDirPath + '../itzik_test_key_aws.pem'  # TODO-SETUP: change project key


####### helper functions
def localErrorReturned(stream):
	if stream is None:
		return False
	errStrListSet = set(stream.decode("utf-8").split('\n'))
	if '' in errStrListSet and len(errStrListSet) == 1:
		return False
	else:
		return True


def localExitWithMessageIfError(stream, process, errString):
	if localErrorReturned(stream):
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


def get_instances_IDs(instances):
	ids = []
	for ins in instances:
		ids.append(ins.id)
	return ids


def get_instances_public_IPs(instances):
	IPs = []
	ec2 = boto3.client('ec2')
	for inst_id in instances:
		dnsName = ec2.describe_instances(InstanceIds=[inst_id])['Reservations'][0]['Instances'][0]['PublicIpAddress']
		IPs.append(dnsName)
	return IPs


def terminate_instances(instances):
	print('terminating')
	ec2 = boto3.client('ec2')
	try:
		ec2.terminate_instances(InstanceIds=instances, DryRun=False)
	except Exception as e:
		print(e)


def run_cmd(instance_ip, cmd, time_out=None):
	ssh = paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	# print('cmd - IP: ' + instance_ip)
	ssh.connect(instance_ip, username='ubuntu', key_filename=KEYFILE, timeout=time_out)
	# print("Executing " + cmd)
	stdin, stdout, stderr = ssh.exec_command(cmd, timeout=time_out)
	stdoutStr = stdout.readlines()
	ssh.close()
	if stderr.readlines() != EMPTY_LIST:
		print('Error for the cmd "' + cmd + '":')
		print(stderr.readlines())
		print('Exiting')
		terminate_instances(instances_list)
	return stdoutStr


def send_file_to_ip(instance_ip, localFile, remotePath):
	ssh = paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	# print('scp - IP: ' + instance_ip)
	ssh.connect(instance_ip, username='ubuntu', key_filename=KEYFILE)
	# print("copying  " + localFile)
	scpConnection = SCPClient(ssh.get_transport())
	scpConnection.put(localFile, remotePath)
	scpConnection.close()
	ssh.close()


def get_file_from_ip(instance_ip, remoteFile, localPath):
	ssh = paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	# print('scp - IP: ' + instance_ip)
	ssh.connect(instance_ip, username='ubuntu', key_filename=KEYFILE)
	# print("getting remote file:  " + remoteFile)
	scpConnection = SCPClient(ssh.get_transport())
	scpConnection.get(remoteFile, localPath)
	scpConnection.close()
	ssh.close()


# returns connection for node such that every node is connected to every other node
def getMeshConnections(nodeNumber, numberOfNodes):
	connList = []
	for to_node in range(0, numberOfNodes):
		if to_node == nodeNumber:
			continue
		connList.append(to_node)
	return connList


# returns random connections for that node, and a connection to the next node.
# consistent between run with the same node index and total number of nodes.
def getStaticRandomConnections(nodeNumber, numberOfNodes):
	connSet = set()
	connSet.add((nodeNumber+1) % numberOfNodes)  # node is connected to the following node to ensure full connectivity
	prevLen = len(connSet)
	for conn in range(0, NUMBER_OF_CONNECTIONS - 1):
		rand = hash(SEED_STR)
		iter = 0
		while len(connSet) == prevLen:
			iter += 1
			rand = int(str( int(str(rand)[0:10]) * hash(str(nodeNumber) + ' ' + str(conn) + ' ' + str(iter)) )[0:10])
			# print('rand: ' + str(rand))
			to_node = rand % numberOfNodes
			# print(to_node)
			if to_node == nodeNumber:
				continue
			connSet.add(to_node)
		# print('selected ' + str(to_node))
		prevLen = len(connSet)
	# print('connections for node ' + str(nodeNumber) + ': ' + str(connSet))
	return list(connSet)


# returns random connections for that node, and a connection to the next node.
# changes with each run
def getDynamicRandomConnections(nodeNumber, numberOfNodes):
	connSet = set()
	connSet.add((nodeNumber+1) % numberOfNodes)  # node is connected to the following node to ensure full connectivity
	prevLen = len(connSet)
	for conn in range(0, NUMBER_OF_CONNECTIONS - 1):
		while len(connSet) == prevLen:
			to_node = random.randrange(numberOfNodes)
			if to_node == nodeNumber:
				continue
			connSet.add(to_node)
		prevLen = len(connSet)
	return list(connSet)


def stringToConnFunc(string):
	switcher = {
		'mesh': getMeshConnections,
		'static': getStaticRandomConnections,
		'dynamic': getDynamicRandomConnections
	}
	if {string}.issubset(switcher):
		return switcher.get(string)
	else:
		return None


confDefault = [
	'regtest=1',
	'rpcuser=rpc',
	'rpcpassword=rpc',
	'server=1',
	'listen=1',
	'dbcache=4',
	'datadir=' + remoteDataDirPath,
	'blocknotify=sudo ' + remoteBaseDirPath + 'block.py %s',
	'blocksonly=1',
	'mempoolexpiry=' + str(math.floor((datetime.now() - datetime(2019, 3, 1))/timedelta(hours=1)))  # default is 2 weeks
]

confRegtest = []


bitcoindCmdArgs = [
	remoteBinPath + bitcoindFileName,
	'-daemon',
	'-reindex-chainstate',
	'-conf=' + remoteBaseDirPath + 'bitcoin.conf'
	]

cliCmdArgs = [
	remoteBinPath + bitcoin_cliFileName,
	'-rpcuser=rpc',
	'-rpcpassword=rpc',
	'-rpcport=18443'  # default rpc port for regtest
	]


####### get args and check them

block_size_MB = float(sys.argv[1])
if ((block_size_MB*BYTES_IN_MB)/TYPICAL_TX_SIZE_BYTES) < 1:
	sys.stderr.write("block size is too small\n")
	sys.exit(1)
utxo_size_of_db_cache_size_percentage = float(sys.argv[2])
if utxo_size_of_db_cache_size_percentage < 0:
	sys.stderr.write("UTXO size must be non-negative\n")
	sys.exit(1)
num_clients = int((sys.argv[3]))
if num_clients <= NUMBER_OF_CONNECTIONS:
	sys.stderr.write('number of clients must be greater than number of connections (' + str(NUMBER_OF_CONNECTIONS) + ')\n')
	sys.exit(1)
connectivity = sys.argv[4]
connFunc = stringToConnFunc(connectivity)
if connFunc is None:
	sys.stderr.write('connectivity type string can only be one of the following:\n')
	sys.stderr.write('mesh - all nodes are connected to all other nodes\n')
	sys.stderr.write('static - ' + str(NUMBER_OF_CONNECTIONS) + ' random connections for each node, consistant between runs\n')
	sys.stderr.write('dynamic - ' + str(NUMBER_OF_CONNECTIONS) + ' random connections for each node, changes every run\n')
	sys.exit(1)



####### make data dir if not found
os.chdir(localBaseDirPath+'../')
if 'data_dirs' not in os.listdir('.'):
	os.mkdir('data_dirs')
os.chdir(nodesPath + '/../data_dirs/')
utxo_size_MB = DEFAULT_DB_CHACHE_SIZE_MB * (utxo_size_of_db_cache_size_percentage / 100)
utxo_set_size = math.floor((utxo_size_MB * BYTES_IN_MB) / TYPICAL_UTXO_SIZE_BYTES)
print('utxo set size is ' + str(utxo_set_size))
print('utxo set size in MB is ' + str(utxo_size_MB))

MAX_TX_IN_BLOCK = math.floor((block_size_MB * BYTES_IN_MB) / TYPICAL_TX_SIZE_BYTES)
print('Txs in block is ' + str(MAX_TX_IN_BLOCK))
print('block size in MB is ' + str(block_size_MB))

dataDirCreated = False
dataDirName = 'utxo-size-MB=' + str(utxo_size_MB)[0:5] + '_block-size-MB=' + str(block_size_MB)[0:5]
if dataDirName not in os.listdir('.'):
	makeDirCmdArgs = [
		'python3.7',
		'create_starting_blockchain.py',
		str(block_size_MB),
		str(utxo_size_of_db_cache_size_percentage)
	]
	os.chdir(localBaseDirPath)
	print('running create_starting_blockchain.py script')
	makeDirRes = subprocess.run(makeDirCmdArgs, capture_output=False)
	localExitWithMessageIfError(makeDirRes.stderr, None, 'Error making data dir')
	print('creation of initial blockchain done.\n\n\n')

	# tar all files
	os.chdir(nodesPath + '/../data_dirs/')
	tarFullCmdArgs = [
		'tar',
		'-czvf',
		TAR_FILE_FULL_NAME,
		'--exclude=*.conf',
		dataDirName
		]
	tarFullRes = subprocess.run(tarFullCmdArgs, capture_output=False, stdout=subprocess.DEVNULL)
	localExitWithMessageIfError(tarFullRes.stderr, None, 'Error making full tar file')
	debugPrint('created full tar file')

	# tar no-mempool files
	tarNoMempoolCmdArgs = [
		'tar',
		'-czvf',
		TAR_FILE_NO_MEMPOOL_NAME,
		'--exclude=*.conf',
		'--exclude=mempool.dat',
		dataDirName,
		]
	tarNoMempoolRes = subprocess.run(tarNoMempoolCmdArgs, capture_output=False, stdout=subprocess.DEVNULL)
	localExitWithMessageIfError(tarNoMempoolRes.stderr, None, 'Error making no-mempool tar file')
	debugPrint('created partial tar file')

	dataDirCreated = True


####### Create AWS instances:
instances_list = []
ec2_rec = boto3.resource('ec2')
for instNum in range(0, num_clients):
	try:
		inst_num_str = str(instNum).zfill(2)
		key_val = 'ttis-inst_' + inst_num_str
		intra_ip_addr = PRIVATE_IP_PREFIX + inst_num_str
		inst = ec2_rec.create_instances(
			ImageId='ami-0a234ad40e779e3cd',  # TODO-SETUP: change AMI if needed to add data directory
			InstanceType='t2.micro',
			KeyName='itzik_test_key',  # TODO-SETUP: change project key
			MaxCount=1,
			MinCount=1,
			TagSpecifications=[
				{
					'ResourceType': 'instance',
					'Tags': [
						{
							'Key': 'Name',
							'Value': key_val
						},
					]
				},
			],
			NetworkInterfaces=[	# TODO-SETUP: change subnet and security group
				{"DeviceIndex": 0, "SubnetId": "subnet-08db8bec756dcb30a", "PrivateIpAddress": intra_ip_addr, "Groups": ['sg-06523c97735030cf4']}
			],
			)
		instances_list.append(inst[0].id)
	except Exception as error:
		print(error)
		terminate_instances(instances_list)
		sys.exit(1)

# debugPrint(instances_list)
print('waiting for instances to finish loading...')
time.sleep(45)
instances_public_ips_list = get_instances_public_IPs(instances_list)

####### clean data directories of nodes
# for instNum in range(0, num_clients):
# 	run_cmd(instances_list[instNum].public_ip_address, 'rm -rf ~/project/data_dir')

####### prepare files at instances
print('preparing data dirs at instances...')
if dataDirCreated:
	# copy tar to remote node
	for node in range(0, num_clients):
		if node == 0:
			localTarFilePath = localBaseDirPath + '../data_dirs/' + TAR_FILE_FULL_NAME
		else:
			localTarFilePath = localBaseDirPath + '../data_dirs/' + TAR_FILE_NO_MEMPOOL_NAME
		try:
			send_file_to_ip(instances_public_ips_list[node], localTarFilePath, remoteBaseDirPath)
		except Exception as error:
			print(error)
			terminate_instances(instances_list)
			sys.exit(1)
	debugPrint('	copied tar files')

	# extract tar
	for node in range(0, num_clients):
		if node == 0:
			remoteTarFilePath = remoteBaseDirPath + TAR_FILE_FULL_NAME
		else:
			remoteTarFilePath = remoteBaseDirPath + TAR_FILE_NO_MEMPOOL_NAME
		run_cmd(instances_public_ips_list[node], 'tar -xvf ' + remoteTarFilePath + ' -C ' + remoteBaseDirPath)
	debugPrint('	extracted tar files')

	# rename dir
	for node in range(0, num_clients):
		run_cmd(instances_public_ips_list[node], 'mv ' + remoteBaseDirPath + dataDirName + ' ' + remoteBaseDirPath + 'dataDir')
	debugPrint('	renamed dirs')

else:
	# copy previously prepared data as data dir
	for node in range(0, num_clients):
		try:
			run_cmd(instances_public_ips_list[node], 'cp -r ' + remoteBaseDirPath + '/data_dirs/' + dataDirName + ' ' + remoteBaseDirPath + 'dataDir')
		except Exception as error:
			print(error)
			terminate_instances(instances_list)
			sys.exit(1)
		run_cmd(instances_public_ips_list[node], 'rm ' + remoteDataDirPath + '*.conf')
		if node != 0:
			run_cmd(instances_public_ips_list[node], 'rm ' + remoteDataDirPath + 'regtest/mempool.dat')
	debugPrint('	copied previously created dataDir from within image')

# copy server.py and block.py scripts
for node in range(0, num_clients):
		if node == 0:
			try:
				send_file_to_ip(instances_public_ips_list[node], localBaseDirPath + 'server.py', remoteBaseDirPath)
				run_cmd(instances_public_ips_list[node], 'chmod 777 ' + remoteBaseDirPath + 'server.py')
			except Exception as error:
				print(error)
				terminate_instances(instances_list)
				sys.exit(1)
		try:
			send_file_to_ip(instances_public_ips_list[node], localBaseDirPath + 'block.py', remoteBaseDirPath)
			run_cmd(instances_public_ips_list[node], 'chmod 777 ' + remoteBaseDirPath + 'block.py')
		except Exception as error:
			print(error)
			terminate_instances(instances_list)
			sys.exit(1)
debugPrint('	copied blocknotify related scripts')


print('making conf files and running nodes...')
# make conf files and start clients
for node in range(0, num_clients):

	# create default section of conf file
	confThisNode = confDefault.copy()
	if node == 0:
		confThisNode[8] = 'blocksonly=0'

	# create [regtest] section of conf file
	confThisNodeRegtest = confRegtest.copy()
	nodes_connections_list = connFunc(node, num_clients)
	for toNode in nodes_connections_list:
		confThisNodeRegtest.append('connect=' + PRIVATE_IP_PREFIX + str(toNode).zfill(2))

	# create conf file from sections
	content = '\n'.join(confThisNode)
	contentRegTest = '\n'.join(confThisNodeRegtest)
	confFilePath = localBaseDirPath + '/../bitcoin.conf'
	with open(confFilePath, "w") as text_file:
		text_file.write(content)
		text_file.write('\n\n[regtest]\n' + contentRegTest + '\n')

	# send conf file
	try:
		send_file_to_ip(instances_public_ips_list[node], confFilePath, remoteBaseDirPath)
	except Exception as error:
		print(error)
		terminate_instances(instances_list)
		sys.exit(1)

	# run bitcoind on remote node
	runBitcoindCmd = ' '.join(bitcoindCmdArgs)
	run_cmd(instances_public_ips_list[node], runBitcoindCmd)

print('finished calling bitcoind on remote nodes')
time.sleep(5)


####### make sure all node are synced
# get miner's best block hash
bestBlockCmdArgs = cliCmdArgs.copy()
bestBlockCmdArgs.append('getbestblockhash')
bestBlockCmd = ' '.join(bestBlockCmdArgs)
bestBlockRet = run_cmd(instances_public_ips_list[0], bestBlockCmd)
bestBlockHashMinerNode = bestBlockRet

# verify all other nodes have the same best block
for node in range(1, num_clients):
	bestBlockRet = run_cmd(instances_public_ips_list[node], bestBlockCmd)
	bestBlockHashThisNode = bestBlockRet
	if bestBlockHashThisNode != bestBlockHashMinerNode:
		input('blockchains are not synced, press enter to terminate...')
		terminate_instances(instances_list)
		sys.exit("nodes' blockchain are not synced")
debugPrint("	all node are synced")

# input('press enter to start timing')

# start server script for timing
print('running server on node 0 (the miner)...')
runServerCmdArgs = [
	'nohup',
	'python3.7',
	remoteBaseDirPath + 'server.py',
	str(num_clients),
	remoteBaseDirPath,
	'>/dev/null',
	'2>/dev/null',
	'&'
]
runServerCmd = ' '.join(runServerCmdArgs)
bestBlockRet = run_cmd(instances_public_ips_list[0], runServerCmd, 15)
startTime = time.time()


# generate block for timing
generateCmdArgs = cliCmdArgs.copy()
generateCmdArgs.append('generate')  # cmd
generateCmdArgs.append('1')  # amount
generateCmd = ' '.join(generateCmdArgs)
run_cmd(instances_public_ips_list[0], generateCmd)
print('generated block for timing')

# wait until server is done timing (all nodes got block)
while True:
	try:
		get_file_from_ip(instances_public_ips_list[0], remoteBaseDirPath + 'time.txt', localBaseDirPath + '../')
	except Exception as error:
		if (time.time() - startTime) > 30:
			input("server took too much time to finish, press enter to terminate...")
			terminate_instances(instances_list)
			sys.exit("server took too much time to finish")
		else:
			time.sleep(0.5)
			continue
	break

print('server finished')
with open(localBaseDirPath + '../time.txt') as f:
	timeGot = f.read()
	debugPrint('	times:\n' + str(timeGot))


# input("Press Enter to terminate AWS machines")
terminate_instances(instances_list)
print("terminated")
sys.exit(0)
