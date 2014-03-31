# Copyright (c) 2006-2009 Mitch Garnaat http://garnaat.org/
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

from boto.mashups.interactive import interactive_shell
import boto
import os
import time
import shutil
import StringIO
import paramiko
import socket
import subprocess


class SSHClient(object):

    def __init__(self, server,
                 host_key_file='~/.ssh/known_hosts',
                 uname='root', timeout=None, ssh_pwd=None):
        self.server = server
        self.host_key_file = host_key_file
        self.uname = uname
        self._timeout = timeout
        self._pkey = paramiko.RSAKey.from_private_key_file(server.ssh_key_file,
                                                           password=ssh_pwd)
        self._ssh_client = paramiko.SSHClient()
        self._ssh_client.load_system_host_keys()
        self._ssh_client.load_host_keys(os.path.expanduser(host_key_file))
        self._ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.connect()

    def connect(self, num_retries=5):
        retry = 0
        while retry < num_retries:
            try:
                self._ssh_client.connect(self.server.hostname,
                                         username=self.uname,
                                         pkey=self._pkey,
                                         timeout=self._timeout)
                return
            except socket.error, (value, message):
                if value in (51, 61, 111):
                    print 'SSH Connection refused, will retry in 5 seconds'
                    time.sleep(5)
                    retry += 1
                else:
                    raise
            except paramiko.BadHostKeyException:
                print "%s has an entry in ~/.ssh/known_hosts and it doesn't match" % self.server.hostname
                print 'Edit that file to remove the entry and then hit return to try again'
                raw_input('Hit Enter when ready')
                retry += 1
            except EOFError:
                print 'Unexpected Error from SSH Connection, retry in 5 seconds'
                time.sleep(5)
                retry += 1
        print 'Could not establish SSH connection'

    def open_sftp(self):
        return self._ssh_client.open_sftp()

    def get_file(self, src, dst):
        sftp_client = self.open_sftp()
        sftp_client.get(src, dst)

    def put_file(self, src, dst):
        sftp_client = self.open_sftp()
        sftp_client.put(src, dst)

    def open(self, filename, mode='r', bufsize=-1):
        """
        Open a file on the remote system and return a file-like object.
        """
        sftp_client = self.open_sftp()
        return sftp_client.open(filename, mode, bufsize)

    def listdir(self, path):
        sftp_client = self.open_sftp()
        return sftp_client.listdir(path)

    def isdir(self, path):
        status = self.run('[ -d %s ] || echo "FALSE"' % path)
        if status[1].startswith('FALSE'):
            return 0
        return 1

    def exists(self, path):
        status = self.run('[ -a %s ] || echo "FALSE"' % path)
        if status[1].startswith('FALSE'):
            return 0
        return 1

    def shell(self):
        """
        Start an interactive shell session on the remote host.
        """
        channel = self._ssh_client.invoke_shell()
        interactive_shell(channel)

    def run(self, command):
        """
        Execute a command on the remote host.  Return a tuple containing
        an integer status and two strings, the first containing stdout
        and the second containing stderr from the command.
        """
        boto.log.debug('running:%s on %s' % (command, self.server.instance_id))
        status = 0
        try:
            t = self._ssh_client.exec_command(command)
        except paramiko.SSHException:
            status = 1
        std_out = t[1].read()
        std_err = t[2].read()
        t[0].close()
        t[1].close()
        t[2].close()
        boto.log.debug('stdout: %s' % std_out)
        boto.log.debug('stderr: %s' % std_err)
        return (status, std_out, std_err)

    def run_pty(self, command):
        """
        Execute a command on the remote host with a pseudo-terminal.
        Returns a string containing the output of the command.
        """
        boto.log.debug('running:%s on %s' % (command, self.server.instance_id))
        channel = self._ssh_client.get_transport().open_session()
        channel.get_pty()
        channel.exec_command(command)
        return channel

    def close(self):
        transport = self._ssh_client.get_transport()
        transport.close()
        self.server.reset_cmdshell()

class LocalClient(object):

    def __init__(self, server, host_key_file=None, uname='root'):
        self.server = server
        self.host_key_file = host_key_file
        self.uname = uname

    def get_file(self, src, dst):
        shutil.copyfile(src, dst)

    def put_file(self, src, dst):
        shutil.copyfile(src, dst)

    def listdir(self, path):
        return os.listdir(path)

    def isdir(self, path):
        return os.path.isdir(path)

    def exists(self, path):
        return os.path.exists(path)

    def shell(self):
        raise NotImplementedError('shell not supported with LocalClient')

    def run(self):
        boto.log.info('running:%s' % self.command)
        log_fp = StringIO.StringIO()
        process = subprocess.Popen(self.command, shell=True, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while process.poll() is None:
            time.sleep(1)
            t = process.communicate()
            log_fp.write(t[0])
            log_fp.write(t[1])
        boto.log.info(log_fp.getvalue())
        boto.log.info('output: %s' % log_fp.getvalue())
        return (process.returncode, log_fp.getvalue())

    def close(self):
        pass

class FakeServer(object):
    """
    A little class to fake out SSHClient (which is expecting a
    :class`boto.manage.server.Server` instance.  This allows us
    to
    """
    def __init__(self, instance, ssh_key_file):
        self.instance = instance
        self.ssh_key_file = ssh_key_file
        self.hostname = instance.dns_name
        self.instance_id = self.instance.id

def start(server):
    instance_id = boto.config.get('Instance', 'instance-id', None)
    if instance_id == server.instance_id:
        return LocalClient(server)
    else:
        return SSHClient(server)

def sshclient_from_instance(instance, ssh_key_file,
                            host_key_file='~/.ssh/known_hosts',
                            user_name='root', ssh_pwd=None):
    """
    Create and return an SSHClient object given an
    instance object.

    :type instance: :class`boto.ec2.instance.Instance` object
    :param instance: The instance object.

    :type ssh_key_file: str
    :param ssh_key_file: A path to the private key file used
                         to log into instance.

    :type host_key_file: str
    :param host_key_file: A path to the known_hosts file used
                          by the SSH client.
                          Defaults to ~/.ssh/known_hosts
    :type user_name: str
    :param user_name: The username to use when logging into
                      the instance.  Defaults to root.

    :type ssh_pwd: str
    :param ssh_pwd: The passphrase, if any, associated with
                    private key.
    """
    s = FakeServer(instance, ssh_key_file)
    return SSHClient(s, host_key_file, user_name, ssh_pwd)
