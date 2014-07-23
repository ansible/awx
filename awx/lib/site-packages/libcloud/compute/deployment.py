# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Provides generic deployment steps for machines post boot.
"""

from __future__ import with_statement

import os
import binascii

from libcloud.utils.py3 import basestring, PY3


class Deployment(object):
    """
    Base class for deployment tasks.
    """

    def run(self, node, client):
        """
        Runs this deployment task on node using the client provided.

        :type node: :class:`Node`
        :keyword node: Node to operate one

        :type client: :class:`BaseSSHClient`
        :keyword client: Connected SSH client to use.

        :return: :class:`Node`
        """
        raise NotImplementedError(
            'run not implemented for this deployment')

    def _get_string_value(self, argument_name, argument_value):
        if not isinstance(argument_value, basestring) and \
           not hasattr(argument_value, 'read'):
            raise TypeError('%s argument must be a string or a file-like '
                            'object' % (argument_name))

        if hasattr(argument_value, 'read'):
            argument_value = argument_value.read()

        return argument_value


class SSHKeyDeployment(Deployment):
    """
    Installs a public SSH Key onto a server.
    """

    def __init__(self, key):
        """
        :type key: ``str`` or :class:`File` object
        :keyword key: Contents of the public key write or a file object which
                      can be read.
        """
        self.key = self._get_string_value(argument_name='key',
                                          argument_value=key)

    def run(self, node, client):
        """
        Installs SSH key into ``.ssh/authorized_keys``

        See also :class:`Deployment.run`
        """
        client.put(".ssh/authorized_keys", contents=self.key, mode='a')
        return node


class FileDeployment(Deployment):
    """
    Installs a file on the server.
    """

    def __init__(self, source, target):
        """
        :type source: ``str``
        :keyword source: Local path of file to be installed

        :type target: ``str``
        :keyword target: Path to install file on node
        """
        self.source = source
        self.target = target

    def run(self, node, client):
        """
        Upload the file, retaining permissions.

        See also :class:`Deployment.run`
        """
        perms = int(oct(os.stat(self.source).st_mode)[4:], 8)

        with open(self.source, 'rb') as fp:
            content = fp.read()

        client.put(path=self.target, chmod=perms,
                   contents=content)
        return node


class ScriptDeployment(Deployment):
    """
    Runs an arbitrary shell script on the server.

    This step works by first writing the content of the shell script (script
    argument) in a \*.sh file on a remote server and then running that file.

    If you are running a non-shell script, make sure to put the appropriate
    shebang to the top of the script. You are also advised to do that even if
    you are running a plan shell script.
    """

    def __init__(self, script, args=None, name=None, delete=False):
        """
        :type script: ``str``
        :keyword script: Contents of the script to run.

        :type args: ``list``
        :keyword args: Optional command line arguments which get passed to the
                       deployment script file.

        :type name: ``str``
        :keyword name: Name of the script to upload it as, if not specified,
                       a random name will be chosen.

        :type delete: ``bool``
        :keyword delete: Whether to delete the script on completion.
        """
        script = self._get_string_value(argument_name='script',
                                        argument_value=script)

        self.script = script
        self.args = args or []
        self.stdout = None
        self.stderr = None
        self.exit_status = None
        self.delete = delete
        self.name = name

        if self.name is None:
            # File is put under user's home directory
            # (~/libcloud_deployment_<random_string>.sh)
            random_string = binascii.hexlify(os.urandom(4))
            random_string = random_string.decode('ascii')
            self.name = 'libcloud_deployment_%s.sh' % (random_string)

    def run(self, node, client):
        """
        Uploads the shell script and then executes it.

        See also :class:`Deployment.run`
        """
        file_path = client.put(path=self.name, chmod=int('755', 8),
                               contents=self.script)

        # Pre-pend cwd if user specified a relative path
        if self.name[0] != '/':
            base_path = os.path.dirname(file_path)
            name = os.path.join(base_path, self.name)
        else:
            name = self.name

        cmd = name

        if self.args:
            # Append arguments to the command
            cmd = '%s %s' % (name, ' '.join(self.args))
        else:
            cmd = name

        self.stdout, self.stderr, self.exit_status = client.run(cmd)

        if self.delete:
            client.delete(self.name)

        return node


class ScriptFileDeployment(ScriptDeployment):
    """
    Runs an arbitrary shell script from a local file on the server. Same as
    ScriptDeployment, except that you can pass in a path to the file instead of
    the script content.
    """

    def __init__(self, script_file, args=None, name=None, delete=False):
        """
        :type script_file: ``str``
        :keyword script_file: Path to a file containing the script to run.

        :type args: ``list``
        :keyword args: Optional command line arguments which get passed to the
                       deployment script file.


        :type name: ``str``
        :keyword name: Name of the script to upload it as, if not specified,
                       a random name will be chosen.

        :type delete: ``bool``
        :keyword delete: Whether to delete the script on completion.
        """
        with open(script_file, 'rb') as fp:
            content = fp.read()

        if PY3:
            content = content.decode('utf-8')

        super(ScriptFileDeployment, self).__init__(script=content,
                                                   args=args,
                                                   name=name,
                                                   delete=delete)


class MultiStepDeployment(Deployment):
    """
    Runs a chain of Deployment steps.
    """
    def __init__(self, add=None):
        """
        :type add: ``list``
        :keyword add: Deployment steps to add.
        """
        self.steps = []
        self.add(add)

    def add(self, add):
        """
        Add a deployment to this chain.

        :type add: Single :class:`Deployment` or a ``list`` of
                   :class:`Deployment`
        :keyword add: Adds this deployment to the others already in this
        object.
        """
        if add is not None:
            add = add if isinstance(add, (list, tuple)) else [add]
            self.steps.extend(add)

    def run(self, node, client):
        """
        Run each deployment that has been added.

        See also :class:`Deployment.run`
        """
        for s in self.steps:
            node = s.run(node, client)
        return node
