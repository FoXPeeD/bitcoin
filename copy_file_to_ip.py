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

localBaseDirPath = os.getcwd() + '/'
KEYFILE = localBaseDirPath + '../itzik_test_key_aws.pem'  # TODO: change to project key
# localFile = '/home/blkchprj/bitcoin-git/data_dirs/data_dirs.tar.gz'
localFile = '/home/blkchprj/bitcoin-git/bitcoin/src/consensus/consensus.h'
instance_ip = '18.220.135.113'
remotePath = '/home/ubuntu/project'


ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
print('scp - IP: ' + instance_ip)
ssh.connect(instance_ip, username='ubuntu', key_filename=KEYFILE)
print("copying  " + localFile)
scpConnection = SCPClient(ssh.get_transport())
scpConnection.put(localFile, remotePath)
scpConnection.close()
ssh.close()
