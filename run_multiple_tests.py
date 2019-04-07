#!/usr/local/bin/python

import sys
import os
import subprocess
import time
from datetime import datetime


# change these parameters:
numberOfNodes = 20
utxoList = [1, 25, 100, 150]
blockList = [1]
connList = ['mesh']
# connList = ['mesh', 'static', 'dynamic']
repeatMeasurements = 4


# constants
delim = '/'
localBaseDirPath = os.getcwd() + '/'
nodesPath = localBaseDirPath + '../nodes/'
localBinPath = localBaseDirPath + 'src/'
bitcoindFileName = './bitcoind'
bitcoin_cliFileName = './bitcoin-cli'



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




currentDT = datetime.now()
timeStr = currentDT.strftime("%Y-%m-%d_%H:%M:%S")
resultsFilePath = localBaseDirPath + '../results/results_' + timeStr + '.csv'
print('block size,UTXO set size,nodes,topography', file=open(resultsFilePath, 'w'), end='')
for num in range(0, numberOfNodes):
	print(',' + str(num), file=open(resultsFilePath, 'a'), end='')
print('', file=open(resultsFilePath, 'a'))
for conn in connList:
	for utxoSize in utxoList:
		for blockSize in blockList:
			for iteration in range(0, repeatMeasurements):

				# run test
				testCmdArgs = [
						'python3.7',
						'make_setup_test.py',
						str(blockSize),
						str(utxoSize),
						str(numberOfNodes),
						conn
					]
				print('*************************************************')
				print(' '.join(testCmdArgs))
				print('*************************************************')
				testRes = subprocess.run(testCmdArgs, capture_output=False)
				localExitWithMessageIfError(testRes.stderr, None, 'Error running test')

				# move results
				mvTimeCmdArgs = [
						'mv',
						localBaseDirPath + '../time.txt',
						localBaseDirPath + '../results/',
				]
				mvTimeRes = subprocess.run(mvTimeCmdArgs, capture_output=False)
				localExitWithMessageIfError(mvTimeRes.stderr, None, 'Error moving results')

				# change results file name
				resultNameStr = str(blockSize) + '_' + str(utxoSize) + '_' + str(numberOfNodes) + '_' + conn
				fileName = resultNameStr + '.csv'
				nameCmdArgs = [
						'mv',
						localBaseDirPath + '../results/time.txt',
						localBaseDirPath + '../results/' + fileName
				]
				nameRes = subprocess.run(nameCmdArgs, capture_output=False)
				localExitWithMessageIfError(nameRes.stderr, None, 'Error changing name of results file')

				# insert results to all results file
				print(str(blockSize) + ',' + str(utxoSize) + ',' + str(numberOfNodes) + ',' + conn + ',', file=open(resultsFilePath, 'a'), end='')
				with open(localBaseDirPath + '../results/' + fileName) as f:
					output = f.read()
					print(output, file=open(resultsFilePath, 'a'), end='')

				time.sleep(60)  # wait for instances to terminate



print('$ done with all tests $')
