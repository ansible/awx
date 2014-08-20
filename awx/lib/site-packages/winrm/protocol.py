import base64
from datetime import timedelta
import uuid
import xml.etree.ElementTree as ET
from isodate.isoduration import duration_isoformat
import xmltodict
from winrm.transport import HttpPlaintext, HttpKerberos, HttpSSL


class Protocol(object):
    """
    This is the main class that does the SOAP request/response logic. There are a few helper classes, but pretty
    much everything comes through here first.
    """
    DEFAULT_TIMEOUT = 'PT60S'
    DEFAULT_MAX_ENV_SIZE = 153600
    DEFAULT_LOCALE = 'en-US'

    def __init__(self, endpoint, transport='plaintext', username=None, password=None, realm=None, service=None, keytab=None, ca_trust_path=None, cert_pem=None, cert_key_pem=None):
        """
        @param string endpoint: the WinRM webservice endpoint
        @param string transport: transport type, one of 'kerberos' (default), 'ssl', 'plaintext'
        @param string username: username
        @param string password: password
        @param string realm: the Kerberos realm we are authenticating to
        @param string service: the service name, default is HTTP
        @param string keytab: the path to a keytab file if you are using one
        @param string ca_trust_path: Certification Authority trust path
        @param string cert_pem: client authentication certificate file path in PEM format
        @param string cert_key_pem: client authentication certificate key file path in PEM format
        """
        self.endpoint = endpoint
        self.timeout = Protocol.DEFAULT_TIMEOUT
        self.max_env_sz = Protocol.DEFAULT_MAX_ENV_SIZE
        self.locale = Protocol.DEFAULT_LOCALE
        if transport == 'plaintext':
            self.transport = HttpPlaintext(endpoint, username, password)
        elif transport == 'kerberos':
            self.transport = HttpKerberos(endpoint)
        elif transport == 'ssl':
            self.transport = HttpSSL(endpoint, username, password, cert_pem=cert_pem, cert_key_pem=cert_key_pem)
        else:
            raise NotImplementedError()
        self.username = username
        self.password = password
        self.service = service
        self.keytab = keytab
        self.ca_trust_path = ca_trust_path

    def set_timeout(self, seconds):
        """
        Operation timeout, see http://msdn.microsoft.com/en-us/library/ee916629(v=PROT.13).aspx
        @param int seconds: the number of seconds to set the timeout to. It will be converted to an ISO8601 format.
        """
        # in original library there is an alias - op_timeout method
        return duration_isoformat(timedelta(seconds))

    def open_shell(self, i_stream='stdin', o_stream='stdout stderr', working_directory=None, env_vars=None, noprofile=False, codepage=437, lifetime=None, idle_timeout=None):
        """
        Create a Shell on the destination host
        @param string i_stream: Which input stream to open. Leave this alone unless you know what you're doing (default: stdin)
        @param string o_stream: Which output stream to open. Leave this alone unless you know what you're doing (default: stdout stderr)
        @param string working_directory: the directory to create the shell in
        @param dict env_vars: environment variables to set for the shell. Fir instance: {'PATH': '%PATH%;c:/Program Files (x86)/Git/bin/', 'CYGWIN': 'nontsec codepage:utf8'}
        @returns The ShellId from the SOAP response.  This is our open shell instance on the remote machine.
        @rtype string
        """
        rq = {'env:Envelope': self._get_soap_header(
            resource_uri='http://schemas.microsoft.com/wbem/wsman/1/windows/shell/cmd',
            action='http://schemas.xmlsoap.org/ws/2004/09/transfer/Create')}
        header = rq['env:Envelope']['env:Header']
        header['w:OptionSet'] = {
            'w:Option': [
                {
                    '@Name': 'WINRS_NOPROFILE',
                    '#text': str(noprofile).upper() #TODO remove str call
                },
                {
                    '@Name': 'WINRS_CODEPAGE',
                    '#text': str(codepage) #TODO remove str call
                }
            ]
        }

        shell = rq['env:Envelope'].setdefault('env:Body', {}).setdefault('rsp:Shell', {})
        shell['rsp:InputStreams'] = i_stream
        shell['rsp:OutputStreams'] = o_stream

        if working_directory:
            #TODO ensure that rsp:WorkingDirectory should be nested within rsp:Shell
            shell['rsp:WorkingDirectory'] = working_directory
            # TODO: research Lifetime a bit more: http://msdn.microsoft.com/en-us/library/cc251546(v=PROT.13).aspx
            #if lifetime:
            #    shell['rsp:Lifetime'] = iso8601_duration.sec_to_dur(lifetime)
            # TODO: make it so the input is given in milliseconds and converted to xs:duration
        if idle_timeout:
            shell['rsp:IdleTimeOut'] = idle_timeout
        if env_vars:
            env = shell.setdefault('rsp:Environment', {})
            for key, value in env_vars.items():
                env['rsp:Variable'] = {'@Name': key, '#text': value}

        rs = self.send_message(xmltodict.unparse(rq))
        #rs = xmltodict.parse(rs)
        #return rs['s:Envelope']['s:Body']['x:ResourceCreated']['a:ReferenceParameters']['w:SelectorSet']['w:Selector']['#text']
        root = ET.fromstring(rs)
        return next(node for node in root.findall('.//*') if node.get('Name') == 'ShellId').text

    # Helper method for building SOAP Header
    def _get_soap_header(self, action=None, resource_uri=None, shell_id=None, message_id=None):
        if not message_id:
            message_id = uuid.uuid4()
        header = {
            '@xmlns:xsd': 'http://www.w3.org/2001/XMLSchema',
            '@xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            '@xmlns:env': 'http://www.w3.org/2003/05/soap-envelope',

            '@xmlns:a': 'http://schemas.xmlsoap.org/ws/2004/08/addressing',
            '@xmlns:b': 'http://schemas.dmtf.org/wbem/wsman/1/cimbinding.xsd',
            '@xmlns:n': 'http://schemas.xmlsoap.org/ws/2004/09/enumeration',
            '@xmlns:x': 'http://schemas.xmlsoap.org/ws/2004/09/transfer',
            '@xmlns:w': 'http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd',
            '@xmlns:p': 'http://schemas.microsoft.com/wbem/wsman/1/wsman.xsd',
            '@xmlns:rsp': 'http://schemas.microsoft.com/wbem/wsman/1/windows/shell',
            '@xmlns:cfg': 'http://schemas.microsoft.com/wbem/wsman/1/config',

            'env:Header': {
                'a:To': 'http://windows-host:5985/wsman',
                'a:ReplyTo': {
                    'a:Address': {
                        '@mustUnderstand': 'true',
                        '#text': 'http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous'
                    }
                },
                'w:MaxEnvelopeSize': {
                    '@mustUnderstand': 'true',
                    '#text': '153600'
                },
                'a:MessageID': 'uuid:{0}'.format(message_id),
                'w:Locale': {
                    '@mustUnderstand': 'false',
                    '@xml:lang': 'en-US'
                },
                'p:DataLocale': {
                    '@mustUnderstand': 'false',
                    '@xml:lang': 'en-US'
                },
                # TODO: research this a bit http://msdn.microsoft.com/en-us/library/cc251561(v=PROT.13).aspx
                #'cfg:MaxTimeoutms': 600
                'w:OperationTimeout': 'PT60S',
                'w:ResourceURI': {
                    '@mustUnderstand': 'true',
                    '#text': resource_uri
                },
                'a:Action': {
                    '@mustUnderstand': 'true',
                    '#text': action
                }
            }
        }
        if shell_id:
            header['env:Header']['w:SelectorSet'] = {
                'w:Selector': {
                    '@Name': 'ShellId',
                    '#text': shell_id
                }
            }
        return header

    def send_message(self, message):
        # TODO add message_id vs relates_to checking
        # TODO port error handling code
        return self.transport.send_message(message)

    def close_shell(self, shell_id):
        """
        Close the shell
        @param string shell_id: The shell id on the remote machine.  See #open_shell
        @returns This should have more error checking but it just returns true for now.
        @rtype bool
        """
        message_id = uuid.uuid4()
        rq = {'env:Envelope': self._get_soap_header(
            resource_uri='http://schemas.microsoft.com/wbem/wsman/1/windows/shell/cmd',
            action='http://schemas.xmlsoap.org/ws/2004/09/transfer/Delete',
            shell_id=shell_id,
            message_id=message_id)}

        # SOAP message requires empty env:Body
        rq['env:Envelope'].setdefault('env:Body', {})

        rs = self.send_message(xmltodict.unparse(rq))
        root = ET.fromstring(rs)
        relates_to = next(node for node in root.findall('.//*') if node.tag.endswith('RelatesTo')).text
        # TODO change assert into user-friendly exception
        assert uuid.UUID(relates_to.replace('uuid:', '')) == message_id

    def run_command(self, shell_id, command, arguments=(), console_mode_stdin=True, skip_cmd_shell=False):
        """
        Run a command on a machine with an open shell
        @param string shell_id: The shell id on the remote machine.  See #open_shell
        @param string command: The command to run on the remote machine
        @param iterable of string arguments: An array of arguments for this command
        @param bool console_mode_stdin: (default: True)
        @param bool skip_cmd_shell: (default: False)
        @return: The CommandId from the SOAP response.  This is the ID we need to query in order to get output.
        @rtype string
        """
        rq = {'env:Envelope': self._get_soap_header(
            resource_uri='http://schemas.microsoft.com/wbem/wsman/1/windows/shell/cmd',
            action='http://schemas.microsoft.com/wbem/wsman/1/windows/shell/Command',
            shell_id=shell_id)}
        header = rq['env:Envelope']['env:Header']
        header['w:OptionSet'] = {
            'w:Option': [
                {
                    '@Name': 'WINRS_CONSOLEMODE_STDIN',
                    '#text': str(console_mode_stdin).upper()
                },
                {
                    '@Name': 'WINRS_SKIP_CMD_SHELL',
                    '#text': str(skip_cmd_shell).upper()
                }
            ]
        }
        cmd_line = rq['env:Envelope'].setdefault('env:Body', {})\
            .setdefault('rsp:CommandLine', {})
        cmd_line['rsp:Command'] = {'#text': command}
        if arguments:
            cmd_line['rsp:Arguments'] = ' '.join(arguments)

        rs = self.send_message(xmltodict.unparse(rq))
        root = ET.fromstring(rs)
        command_id = next(node for node in root.findall('.//*') if node.tag.endswith('CommandId')).text
        return command_id

    def cleanup_command(self, shell_id, command_id):
        """
        Clean-up after a command. @see #run_command
        @param string shell_id: The shell id on the remote machine.  See #open_shell
        @param string command_id: The command id on the remote machine.  See #run_command
        @returns: This should have more error checking but it just returns true for now.
        @rtype bool
        """
        message_id = uuid.uuid4()
        rq = {'env:Envelope': self._get_soap_header(
            resource_uri='http://schemas.microsoft.com/wbem/wsman/1/windows/shell/cmd',
            action='http://schemas.microsoft.com/wbem/wsman/1/windows/shell/Signal',
            shell_id=shell_id,
            message_id=message_id)}

        # Signal the Command references to terminate (close stdout/stderr)
        signal = rq['env:Envelope'].setdefault('env:Body', {}).setdefault('rsp:Signal', {})
        signal['@CommandId'] = command_id
        signal['rsp:Code'] = \
            'http://schemas.microsoft.com/wbem/wsman/1/windows/shell/signal/terminate'

        rs = self.send_message(xmltodict.unparse(rq))
        root = ET.fromstring(rs)
        relates_to = next(node for node in root.findall('.//*') if node.tag.endswith('RelatesTo')).text
        # TODO change assert into user-friendly exception
        assert uuid.UUID(relates_to.replace('uuid:', '')) == message_id

    def get_command_output(self, shell_id, command_id):
        """
        Get the Output of the given shell and command
        @param string shell_id: The shell id on the remote machine.  See #open_shell
        @param string command_id: The command id on the remote machine.  See #run_command
        #@return [Hash] Returns a Hash with a key :exitcode and :data.  Data is an Array of Hashes where the cooresponding key
        #   is either :stdout or :stderr.  The reason it is in an Array so so we can get the output in the order it ocurrs on
        #   the console.
        """
        stdout_buffer, stderr_buffer = [], []
        command_done = False
        while not command_done:
            stdout, stderr, return_code, command_done = \
                self._raw_get_command_output(shell_id, command_id)
            stdout_buffer.append(stdout)
            stderr_buffer.append(stderr)
        return ''.join(stdout_buffer), ''.join(stderr_buffer), return_code

    def _raw_get_command_output(self, shell_id, command_id):
        rq = {'env:Envelope': self._get_soap_header(
            resource_uri='http://schemas.microsoft.com/wbem/wsman/1/windows/shell/cmd',
            action='http://schemas.microsoft.com/wbem/wsman/1/windows/shell/Receive',
            shell_id=shell_id)}

        stream = rq['env:Envelope'].setdefault('env:Body', {}).setdefault('rsp:Receive', {})\
            .setdefault('rsp:DesiredStream', {})
        stream['@CommandId'] = command_id
        stream['#text'] = 'stdout stderr'

        rs = self.send_message(xmltodict.unparse(rq))
        root = ET.fromstring(rs)
        stream_nodes = [node for node in root.findall('.//*') if node.tag.endswith('Stream')]
        stdout = stderr = ''
        return_code = -1
        for stream_node in stream_nodes:
            if stream_node.text:
                if stream_node.attrib['Name'] == 'stdout':
                    stdout += str(base64.b64decode(stream_node.text.encode('ascii')))
                elif stream_node.attrib['Name'] == 'stderr':
                    stderr += str(base64.b64decode(stream_node.text.encode('ascii')))

        # We may need to get additional output if the stream has not finished.
        # The CommandState will change from Running to Done like so:
        # @example
        #   from...
        #   <rsp:CommandState CommandId="..." State="http://schemas.microsoft.com/wbem/wsman/1/windows/shell/CommandState/Running"/>
        #   to...
        #   <rsp:CommandState CommandId="..." State="http://schemas.microsoft.com/wbem/wsman/1/windows/shell/CommandState/Done">
        #     <rsp:ExitCode>0</rsp:ExitCode>
        #   </rsp:CommandState>
        command_done = len([node for node in root.findall('.//*') if node.get('State', '').endswith('CommandState/Done')]) == 1
        if command_done:
            return_code = int(next(node for node in root.findall('.//*') if node.tag.endswith('ExitCode')).text)

        return stdout, stderr, return_code, command_done
