import paramiko
from scp import SCPClient
import os, sys

KEYFILE='../itzik_test_key_aws.pem'
ip='ec2-18-220-112-216.us-east-2.compute.amazonaws.com'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(ip, username='ubuntu', key_filename=KEYFILE)


stdin, stdout, stderr = ssh.exec_command('pwd')
remoteDir=stdout.readlines()[0].strip()
print(remoteDir)

scpc = SCPClient(ssh.get_transport())
scpc.put('../bitcoin_client.tar','bitcoin_client.tar')
scpc.close()

stdin, stdout, stderr = ssh.exec_command('ls')
print(stdout.readlines())


ssh.close()

