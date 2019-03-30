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
from scp import SCPClient
from datetime import datetime
from datetime import timedelta

# constants
DEFAULT_DB_CHACHE_SIZE_MB = 1.8
TX_DEFAULT_SENT_AMOUNT = 0.0001
BASE_PORT_NUM = 18200
BASE_RPC_PORT_NUM = 9200
LOCAL_HOST = '127.0.0.1'
PRIVATE_IP_PREFIX = '10.0.2.1'
TYPICAL_TX_SIZE_BYTES = 244
TYPICAL_UTXO_SIZE_BYTES = 77
BYTES_IN_MB = 1000000
TAR_FILE_FULL_NAME = 'data-full.tar.gz'
TAR_FILE_NO_MEMPOOL_NAME = 'data-no-mempool.tar.gz'
EMPTY_LIST = []
debug = 1

if len(sys.argv) < 4:
	print('wrong number of arguments')
	sys.stderr.write("wrong number of arguments\n")
	sys.stderr.write("usage:\n")
	sys.stderr.write("1: block size in MB\n")
	sys.stderr.write("2: percentage of utxo size from dbcache\n")
	sys.stderr.write("3: number of clients\n")
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
KEYFILE = localBaseDirPath + '../itzik_test_key_aws.pem'  # TODO: change to project key


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


def sshExitWithMessageIfError(stream, instances, errString):
	if errorReturned(stream):
		print('Error received:')
		print(stream)
		if instances is not None:
			if isinstance(instances, list):
				terminate_instances(instances)
			else:
				terminate_instances(instances)
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
	# print(instances)
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


def getMeshConnections(nodeNumber, numberOfNodes):
	connList = []
	for to_node in range(0, numberOfNodes):
		if to_node == nodeNumber:
			continue
		connList.append(to_node)
	return connList


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
	# 'maxmempool=4'
]

confRegtest = [
	# 'port=' + str(BASE_PORT_NUM),
	# 'rpcport=' + str(BASE_RPC_PORT_NUM)
]


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
# num_clients = 3
num_clients = int((sys.argv[3]))
if num_clients < 2:
	sys.stderr.write("number of clients must be greater than 1\n")
	sys.exit(1)
# block_size_MB = 0.025
block_size_MB = float(sys.argv[1])
if ((block_size_MB*BYTES_IN_MB)/TYPICAL_TX_SIZE_BYTES) < 1:
	sys.stderr.write("block size is too small\n")
	sys.exit(1)
# utxo_size_of_db_cache_size_percentage = 0.1
utxo_size_of_db_cache_size_percentage = float(sys.argv[2])
if utxo_size_of_db_cache_size_percentage < 0:
	sys.stderr.write("UTXO size must be non-negative\n")
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
dataDirName = 'utxo-size-MB=' + str(utxo_size_MB) + '_block-size-MB=' + str(block_size_MB)
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

	# time.sleep(2)
	# subprocess.run(['ls'], capture_output=False)
	# chmodRes = subprocess.run(['chmod', '555', TAR_FILE_FULL_NAME], capture_output=False)
	# localExitWithMessageIfError(chmodRes.stderr, None, 'Error chmod full tar file')
	# chmodRes = subprocess.run(['chmod', '555', TAR_FILE_NO_MEMPOOL_NAME], capture_output=False)
	# localExitWithMessageIfError(chmodRes.stderr, None, 'Error chmod no-mempool tar file')

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
			ImageId='ami-0b1650b9ad3f7a939',
			# ImageId='ami-0a52acf469d39b2ce',
			InstanceType='t2.micro',
			KeyName='itzik_test_key',  # TODO: change to project key
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
			NetworkInterfaces=[
				{"DeviceIndex": 0, "SubnetId": "subnet-08db8bec756dcb30a", "PrivateIpAddress": intra_ip_addr, "Groups": ['sg-06523c97735030cf4']}
			],
			)
		# debugPrint('	started instance ' + str(instNum))
		instances_list.append(inst[0].id)
	except Exception as error:
		print(error)
		terminate_instances(instances_list)
		sys.exit(1)

# debugPrint(instances_list)
# TODO: wait for instances to finish loading
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
			sys.exit(0)
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
		# confThisNode[10] = 'maxmempool=32'

	# create [regtest] section of conf file
	confThisNodeRegtest = confRegtest.copy()
	# confThisNodeRegtest[0] = 'port=' + str(BASE_PORT_NUM + node)
	# confThisNodeRegtest[1] = 'rpcport=' + str(BASE_RPC_PORT_NUM + node)
	nodes_connections_list = getMeshConnections(node, num_clients)
	for toNode in nodes_connections_list:
		# confThisNodeRegtest.append('connect=' + PRIVATE_IP_PREFIX + str(toNode).zfill(2) + ':' + str(BASE_PORT_NUM + toNode))
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
	# input('check conf file, press enter to continue')
	run_cmd(instances_public_ips_list[node], runBitcoindCmd)

print('finished calling bitcoind on remote nodes')
time.sleep(5)


# make sure all node are synced getbestblockhash
bestBlockCmdArgs = cliCmdArgs.copy()
bestBlockCmdArgs.append('getbestblockhash')
bestBlockCmd = ' '.join(bestBlockCmdArgs)
bestBlockRet = run_cmd(instances_public_ips_list[0], bestBlockCmd)
bestBlockHashMinerNode = bestBlockRet
# bestBlockHashMinerNode = '"' + bestBlockRet.stdout.decode("utf-8").split()[0] + '"'

for node in range(1, num_clients):
	# rpcport = BASE_RPC_PORT_NUM + node
	# bestBlockCmdArgs[3] = '-rpcport=' + str(rpcport)
	bestBlockRet = run_cmd(instances_public_ips_list[node], bestBlockCmd)
	bestBlockHashThisNode = bestBlockRet
	# bestBlockHashThisNode = '"' + bestBlockRet.stdout.decode("utf-8").split()[0] + '"'
	if bestBlockHashThisNode != bestBlockHashMinerNode:
		input('blockchains are not synced, press enter to terminate...')
		terminate_instances(instances_list)
		sys.exit("nodes' blockchain are not synced")
debugPrint("	all node are synced")

input('press enter to start timing')

# start script for timing
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
		if (time.time() - startTime) > 15:
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


input("Press Enter to terminate AWS machines")
terminate_instances(instances_list)
print("terminated")
