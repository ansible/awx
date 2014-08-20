import sys
import base64
from winrm.exceptions import WinRMTransportError

HAVE_KERBEROS=False
try:
    import kerberos
    HAVE_KERBEROS=True
except ImportError:
    pass

is_py2 = sys.version[0] == '2'
if is_py2:
    from urllib2 import Request, URLError, HTTPError, HTTPBasicAuthHandler, HTTPPasswordMgrWithDefaultRealm, HTTPSHandler
    from urllib2 import urlopen, build_opener, install_opener
    from urlparse import urlparse
    from httplib import HTTPSConnection
else:
    from urllib.request import Request, URLError, HTTPError, HTTPBasicAuthHandler, HTTPPasswordMgrWithDefaultRealm, HTTPSHandler
    from urllib.request import urlopen, build_opener, install_opener
    from urllib.parse import urlparse
    from http.client import HTTPSConnection


class HttpTransport(object):
    def __init__(self, endpoint, username, password):
        self.endpoint = endpoint
        self.username = username
        self.password = password
        self.user_agent =  'Python WinRM client'
        self.timeout = 3600 # Set this to an unreasonable amount for now because WinRM has timeouts

    def basic_auth_only(self):
        #here we should remove handler for any authentication handlers other than basic
        # but maybe leave original credentials

        # auths = @httpcli.www_auth.instance_variable_get('@authenticator')
        # auths.delete_if {|i| i.scheme !~ /basic/i}
        # drop all variables in auths if they not contains "basic" as insensitive.
        pass

    def no_sspi_auth(self):
        # here we should remove handler for Negotiate/NTLM negotiation
        # but maybe leave original credentials
        pass


class HttpPlaintext(HttpTransport):
    def __init__(self, endpoint, username='', password='', disable_sspi=True, basic_auth_only=True):
        super(HttpPlaintext, self).__init__(endpoint, username, password)
        if disable_sspi:
            self.no_sspi_auth()
        if basic_auth_only:
            self.basic_auth_only()

        self._headers = {'Content-Type' : 'application/soap+xml;charset=UTF-8',
                         'User-Agent' : 'Python WinRM client'}

    def _setup_opener(self):
        password_manager = HTTPPasswordMgrWithDefaultRealm()
        password_manager.add_password(None, self.endpoint, self.username, self.password)
        auth_manager = HTTPBasicAuthHandler(password_manager)
        opener = build_opener(auth_manager)
        install_opener(opener)

    def send_message(self, message):
        headers = self._headers.copy()
        headers['Content-Length'] = len(message)

        self._setup_opener()
        request = Request(self.endpoint, data=message, headers=headers)
        try:
            response = urlopen(request, timeout=self.timeout)
            # Version 1.1 of WinRM adds the namespaces in the document instead of the envelope so we have to
            # add them ourselves here. This should have no affect version 2.
            response_text = response.read()
            return response_text
            #doc = ElementTree.fromstring(response.read())
            #Ruby
            #doc = Nokogiri::XML(resp.http_body.content)
            #doc.collect_namespaces.each_pair do |k,v|
            #    doc.root.add_namespace((k.split(/:/).last),v) unless doc.namespaces.has_key?(k)
            #end
            #return doc
            #return doc
        except HTTPError as ex:
            response_text = ex.read()
            # Per http://msdn.microsoft.com/en-us/library/cc251676.aspx rule 3,
            # should handle this 500 error and retry receiving command output.
            if 'http://schemas.microsoft.com/wbem/wsman/1/windows/shell/Receive' in message and 'Code="2150858793"' in response_text:
                return response_text
            error_message = 'Bad HTTP response returned from server. Code {0}'.format(ex.code)
            if ex.msg:
                error_message += ', {0}'.format(ex.msg)
            raise WinRMTransportError(error_message)
        except URLError as ex:
            raise WinRMTransportError(ex.reason)


class HTTPSClientAuthHandler(HTTPSHandler):
    def __init__(self, cert, key):
        HTTPSHandler.__init__(self)
        self.cert = cert
        self.key = key

    def https_open(self, req):
        return self.do_open(self.getConnection, req)

    def getConnection(self, host, timeout=300):
        return HTTPSConnection(host, key_file=self.key, cert_file=self.cert)


class HttpSSL(HttpPlaintext):
    """Uses SSL to secure the transport"""
    def __init__(self, endpoint, username, password, ca_trust_path=None, disable_sspi=True, basic_auth_only=True,
                 cert_pem=None, cert_key_pem=None):
        super(HttpSSL, self).__init__(endpoint, username, password)

        self._cert_pem = cert_pem
        self._cert_key_pem = cert_key_pem

        #Ruby
        #@httpcli.set_auth(endpoint, user, pass)
        #@httpcli.ssl_config.set_trust_ca(ca_trust_path) unless ca_trust_path.nil?
        if disable_sspi:
            self.no_sspi_auth()
        if basic_auth_only:
            self.basic_auth_only()

        if self._cert_pem:
            self._headers['Authorization'] = "http://schemas.dmtf.org/wbem/wsman/1/wsman/secprofile/https/mutual"

    def _setup_opener(self):
        if not self._cert_pem:
            super(HttpSSL, self)._setup_opener()
        else:
            opener = build_opener(HTTPSClientAuthHandler(self._cert_pem, self._cert_key_pem))
            install_opener(opener)


class KerberosTicket:
    """
    Implementation based on http://ncoghlan_devs-python-notes.readthedocs.org/en/latest/python_kerberos.html
    """
    def __init__(self, service):
        ignored_code, krb_context = kerberos.authGSSClientInit(service)
        kerberos.authGSSClientStep(krb_context, '')
        # TODO authGSSClientStep may raise following error:
        #GSSError: (('Unspecified GSS failure.  Minor code may provide more information', 851968), ("Credentials cache file '/tmp/krb5cc_1000' not found", -1765328189))
        self._krb_context = krb_context
        gss_response = kerberos.authGSSClientResponse(krb_context)
        self.auth_header = 'Negotiate {0}'.format(gss_response)

    def verify_response(self, auth_header):
        # Handle comma-separated lists of authentication fields
        for field in auth_header.split(','):
            kind, ignored_space, details = field.strip().partition(' ')
            if kind.lower() == 'negotiate':
                auth_details = details.strip()
                break
        else:
            raise ValueError('Negotiate not found in {0}'.format(auth_header))
            # Finish the Kerberos handshake
        krb_context = self._krb_context
        if krb_context is None:
            raise RuntimeError('Ticket already used for verification')
        self._krb_context = None
        kerberos.authGSSClientStep(krb_context, auth_details)
        #print('User {0} authenticated successfully using Kerberos authentication'.format(kerberos.authGSSClientUserName(krb_context)))
        kerberos.authGSSClientClean(krb_context)


class HttpKerberos(HttpTransport):
    def __init__(self, endpoint, realm=None, service='HTTP', keytab=None):
        """
        Uses Kerberos/GSS-API to authenticate and encrypt messages
        @param string endpoint: the WinRM webservice endpoint
        @param string realm: the Kerberos realm we are authenticating to
        @param string service: the service name, default is HTTP
        @param string keytab: the path to a keytab file if you are using one
        """
        if not HAVE_KERBEROS:
            raise WinRMTransportError('kerberos is not installed')

        super(HttpKerberos, self).__init__(endpoint, None, None)
        self.krb_service = '{0}@{1}'.format(service, urlparse(endpoint).hostname)
        #self.krb_ticket = KerberosTicket(krb_service)

    def set_auth(self, username, password):
        raise NotImplementedError

    def send_message(self, message):
        # TODO current implementation does negotiation on each HTTP request which is not efficient
        # TODO support kerberos session with message encryption
        krb_ticket = KerberosTicket(self.krb_service)
        headers = {'Authorization': krb_ticket.auth_header,
                   'Connection': 'Keep-Alive',
                   'Content-Type': 'application/soap+xml;charset=UTF-8',
                   'User-Agent': 'Python WinRM client'}

        request = Request(self.endpoint, data=message, headers=headers)
        try:
            response = urlopen(request, timeout=self.timeout)
            krb_ticket.verify_response(response.headers['WWW-Authenticate'])
            response_text = response.read()
            return response_text
        except HTTPError as ex:
            response_text = ex.read()
            # Per http://msdn.microsoft.com/en-us/library/cc251676.aspx rule 3,
            # should handle this 500 error and retry receiving command output.
            if 'http://schemas.microsoft.com/wbem/wsman/1/windows/shell/Receive' in message and 'Code="2150858793"' in response_text:
                return response_text
            #if ex.code == 401 and ex.headers['WWW-Authenticate'] == 'Negotiate, Basic realm="WSMAN"':
            error_message = 'Kerberos-based authentication was failed. Code {0}'.format(ex.code)
            if ex.msg:
                error_message += ', {0}'.format(ex.msg)
            raise WinRMTransportError(error_message)
        except URLError as ex:
            raise WinRMTransportError(ex.reason)

    def _winrm_encrypt(self, string):
        """
        @returns the encrypted request string
        @rtype string
        """
        raise NotImplementedError

    def _winrm_decrypt(self, string):
        raise NotImplementedError
