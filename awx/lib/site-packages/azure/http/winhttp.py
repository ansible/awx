#-------------------------------------------------------------------------
# Copyright (c) Microsoft.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#--------------------------------------------------------------------------
from ctypes import (
    c_void_p,
    c_long,
    c_ulong,
    c_longlong,
    c_ulonglong,
    c_short,
    c_ushort,
    c_wchar_p,
    c_byte,
    byref,
    Structure,
    Union,
    POINTER,
    WINFUNCTYPE,
    HRESULT,
    oledll,
    WinDLL,
    )
import ctypes
import sys

if sys.version_info >= (3,):
    def unicode(text):
        return text

#------------------------------------------------------------------------------
#  Constants that are used in COM operations
VT_EMPTY = 0
VT_NULL = 1
VT_I2 = 2
VT_I4 = 3
VT_BSTR = 8
VT_BOOL = 11
VT_I1 = 16
VT_UI1 = 17
VT_UI2 = 18
VT_UI4 = 19
VT_I8 = 20
VT_UI8 = 21
VT_ARRAY = 8192

HTTPREQUEST_PROXYSETTING_PROXY = 2
HTTPREQUEST_SETCREDENTIALS_FOR_PROXY = 1

HTTPREQUEST_PROXY_SETTING = c_long
HTTPREQUEST_SETCREDENTIALS_FLAGS = c_long
#------------------------------------------------------------------------------
# Com related APIs that are used.
_ole32 = oledll.ole32
_oleaut32 = WinDLL('oleaut32')
_CLSIDFromString = _ole32.CLSIDFromString
_CoInitialize = _ole32.CoInitialize
_CoInitialize.argtypes = [c_void_p]

_CoCreateInstance = _ole32.CoCreateInstance

_SysAllocString = _oleaut32.SysAllocString
_SysAllocString.restype = c_void_p
_SysAllocString.argtypes = [c_wchar_p]

_SysFreeString = _oleaut32.SysFreeString
_SysFreeString.argtypes = [c_void_p]

# SAFEARRAY*
# SafeArrayCreateVector(_In_ VARTYPE vt,_In_ LONG lLbound,_In_ ULONG
# cElements);
_SafeArrayCreateVector = _oleaut32.SafeArrayCreateVector
_SafeArrayCreateVector.restype = c_void_p
_SafeArrayCreateVector.argtypes = [c_ushort, c_long, c_ulong]

# HRESULT
# SafeArrayAccessData(_In_ SAFEARRAY *psa, _Out_ void **ppvData);
_SafeArrayAccessData = _oleaut32.SafeArrayAccessData
_SafeArrayAccessData.argtypes = [c_void_p, POINTER(c_void_p)]

# HRESULT
# SafeArrayUnaccessData(_In_ SAFEARRAY *psa);
_SafeArrayUnaccessData = _oleaut32.SafeArrayUnaccessData
_SafeArrayUnaccessData.argtypes = [c_void_p]

# HRESULT
# SafeArrayGetUBound(_In_ SAFEARRAY *psa, _In_ UINT nDim, _Out_ LONG
# *plUbound);
_SafeArrayGetUBound = _oleaut32.SafeArrayGetUBound
_SafeArrayGetUBound.argtypes = [c_void_p, c_ulong, POINTER(c_long)]


#------------------------------------------------------------------------------

class BSTR(c_wchar_p):

    ''' BSTR class in python. '''

    def __init__(self, value):
        super(BSTR, self).__init__(_SysAllocString(value))

    def __del__(self):
        _SysFreeString(self)


class VARIANT(Structure):

    '''
    VARIANT structure in python. Does not match the definition in
    MSDN exactly & it is only mapping the used fields.  Field names are also
    slighty different.
    '''

    class _tagData(Union):

        class _tagRecord(Structure):
            _fields_ = [('pvoid', c_void_p), ('precord', c_void_p)]

        _fields_ = [('llval', c_longlong),
                    ('ullval', c_ulonglong),
                    ('lval', c_long),
                    ('ulval', c_ulong),
                    ('ival', c_short),
                    ('boolval', c_ushort),
                    ('bstrval', BSTR),
                    ('parray', c_void_p),
                    ('record', _tagRecord)]

    _fields_ = [('vt', c_ushort),
                ('wReserved1', c_ushort),
                ('wReserved2', c_ushort),
                ('wReserved3', c_ushort),
                ('vdata', _tagData)]

    @staticmethod
    def create_empty():
        variant = VARIANT()
        variant.vt = VT_EMPTY
        variant.vdata.llval = 0
        return variant

    @staticmethod
    def create_safearray_from_str(text):
        variant = VARIANT()
        variant.vt = VT_ARRAY | VT_UI1

        length = len(text)
        variant.vdata.parray = _SafeArrayCreateVector(VT_UI1, 0, length)
        pvdata = c_void_p()
        _SafeArrayAccessData(variant.vdata.parray, byref(pvdata))
        ctypes.memmove(pvdata, text, length)
        _SafeArrayUnaccessData(variant.vdata.parray)

        return variant

    @staticmethod
    def create_bstr_from_str(text):
        variant = VARIANT()
        variant.vt = VT_BSTR
        variant.vdata.bstrval = BSTR(text)
        return variant

    @staticmethod
    def create_bool_false():
        variant = VARIANT()
        variant.vt = VT_BOOL
        variant.vdata.boolval = 0
        return variant

    def is_safearray_of_bytes(self):
        return self.vt == VT_ARRAY | VT_UI1

    def str_from_safearray(self):
        assert self.vt == VT_ARRAY | VT_UI1
        pvdata = c_void_p()
        count = c_long()
        _SafeArrayGetUBound(self.vdata.parray, 1, byref(count))
        count = c_long(count.value + 1)
        _SafeArrayAccessData(self.vdata.parray, byref(pvdata))
        text = ctypes.string_at(pvdata, count)
        _SafeArrayUnaccessData(self.vdata.parray)
        return text

    def __del__(self):
        _VariantClear(self)

# HRESULT VariantClear(_Inout_ VARIANTARG *pvarg);
_VariantClear = _oleaut32.VariantClear
_VariantClear.argtypes = [POINTER(VARIANT)]


class GUID(Structure):

    ''' GUID structure in python. '''

    _fields_ = [("data1", c_ulong),
                ("data2", c_ushort),
                ("data3", c_ushort),
                ("data4", c_byte * 8)]

    def __init__(self, name=None):
        if name is not None:
            _CLSIDFromString(unicode(name), byref(self))


class _WinHttpRequest(c_void_p):

    '''
    Maps the Com API to Python class functions. Not all methods in
    IWinHttpWebRequest are mapped - only the methods we use.
    '''
    _AddRef = WINFUNCTYPE(c_long) \
        (1, 'AddRef')
    _Release = WINFUNCTYPE(c_long) \
        (2, 'Release')
    _SetProxy = WINFUNCTYPE(HRESULT,
                            HTTPREQUEST_PROXY_SETTING,
                            VARIANT,
                            VARIANT) \
        (7, 'SetProxy')
    _SetCredentials = WINFUNCTYPE(HRESULT,
                                  BSTR,
                                  BSTR,
                                  HTTPREQUEST_SETCREDENTIALS_FLAGS) \
        (8, 'SetCredentials')
    _Open = WINFUNCTYPE(HRESULT, BSTR, BSTR, VARIANT) \
        (9, 'Open')
    _SetRequestHeader = WINFUNCTYPE(HRESULT, BSTR, BSTR) \
        (10, 'SetRequestHeader')
    _GetResponseHeader = WINFUNCTYPE(HRESULT, BSTR, POINTER(c_void_p)) \
        (11, 'GetResponseHeader')
    _GetAllResponseHeaders = WINFUNCTYPE(HRESULT, POINTER(c_void_p)) \
        (12, 'GetAllResponseHeaders')
    _Send = WINFUNCTYPE(HRESULT, VARIANT) \
        (13, 'Send')
    _Status = WINFUNCTYPE(HRESULT, POINTER(c_long)) \
        (14, 'Status')
    _StatusText = WINFUNCTYPE(HRESULT, POINTER(c_void_p)) \
        (15, 'StatusText')
    _ResponseText = WINFUNCTYPE(HRESULT, POINTER(c_void_p)) \
        (16, 'ResponseText')
    _ResponseBody = WINFUNCTYPE(HRESULT, POINTER(VARIANT)) \
        (17, 'ResponseBody')
    _ResponseStream = WINFUNCTYPE(HRESULT, POINTER(VARIANT)) \
        (18, 'ResponseStream')
    _WaitForResponse = WINFUNCTYPE(HRESULT, VARIANT, POINTER(c_ushort)) \
        (21, 'WaitForResponse')
    _Abort = WINFUNCTYPE(HRESULT) \
        (22, 'Abort')
    _SetTimeouts = WINFUNCTYPE(HRESULT, c_long, c_long, c_long, c_long) \
        (23, 'SetTimeouts')
    _SetClientCertificate = WINFUNCTYPE(HRESULT, BSTR) \
        (24, 'SetClientCertificate')

    def open(self, method, url):
        '''
        Opens the request.

        method: the request VERB 'GET', 'POST', etc.
        url: the url to connect
        '''
        _WinHttpRequest._SetTimeouts(self, 0, 65000, 65000, 65000)

        flag = VARIANT.create_bool_false()
        _method = BSTR(method)
        _url = BSTR(url)
        _WinHttpRequest._Open(self, _method, _url, flag)

    def set_request_header(self, name, value):
        ''' Sets the request header. '''

        _name = BSTR(name)
        _value = BSTR(value)
        _WinHttpRequest._SetRequestHeader(self, _name, _value)

    def get_all_response_headers(self):
        ''' Gets back all response headers. '''

        bstr_headers = c_void_p()
        _WinHttpRequest._GetAllResponseHeaders(self, byref(bstr_headers))
        bstr_headers = ctypes.cast(bstr_headers, c_wchar_p)
        headers = bstr_headers.value
        _SysFreeString(bstr_headers)
        return headers

    def send(self, request=None):
        ''' Sends the request body. '''

        # Sends VT_EMPTY if it is GET, HEAD request.
        if request is None:
            var_empty = VARIANT.create_empty()
            _WinHttpRequest._Send(self, var_empty)
        else:  # Sends request body as SAFEArray.
            _request = VARIANT.create_safearray_from_str(request)
            _WinHttpRequest._Send(self, _request)

    def status(self):
        ''' Gets status of response. '''

        status = c_long()
        _WinHttpRequest._Status(self, byref(status))
        return int(status.value)

    def status_text(self):
        ''' Gets status text of response. '''

        bstr_status_text = c_void_p()
        _WinHttpRequest._StatusText(self, byref(bstr_status_text))
        bstr_status_text = ctypes.cast(bstr_status_text, c_wchar_p)
        status_text = bstr_status_text.value
        _SysFreeString(bstr_status_text)
        return status_text

    def response_body(self):
        '''
        Gets response body as a SAFEARRAY and converts the SAFEARRAY to str.
        If it is an xml file, it always contains 3 characters before <?xml,
        so we remove them.
        '''
        var_respbody = VARIANT()
        _WinHttpRequest._ResponseBody(self, byref(var_respbody))
        if var_respbody.is_safearray_of_bytes():
            respbody = var_respbody.str_from_safearray()
            if respbody[3:].startswith(b'<?xml') and\
               respbody.startswith(b'\xef\xbb\xbf'):
                respbody = respbody[3:]
            return respbody
        else:
            return ''

    def set_client_certificate(self, certificate):
        '''Sets client certificate for the request. '''
        _certificate = BSTR(certificate)
        _WinHttpRequest._SetClientCertificate(self, _certificate)

    def set_tunnel(self, host, port):
        ''' Sets up the host and the port for the HTTP CONNECT Tunnelling.'''
        url = host
        if port:
            url = url + u':' + port

        var_host = VARIANT.create_bstr_from_str(url)
        var_empty = VARIANT.create_empty()

        _WinHttpRequest._SetProxy(
            self, HTTPREQUEST_PROXYSETTING_PROXY, var_host, var_empty)

    def set_proxy_credentials(self, user, password):
        _WinHttpRequest._SetCredentials(
            self, BSTR(user), BSTR(password),
            HTTPREQUEST_SETCREDENTIALS_FOR_PROXY)

    def __del__(self):
        if self.value is not None:
            _WinHttpRequest._Release(self)


class _Response(object):

    ''' Response class corresponding to the response returned from httplib
    HTTPConnection. '''

    def __init__(self, _status, _status_text, _length, _headers, _respbody):
        self.status = _status
        self.reason = _status_text
        self.length = _length
        self.headers = _headers
        self.respbody = _respbody

    def getheaders(self):
        '''Returns response headers.'''
        return self.headers

    def read(self, _length):
        '''Returns resonse body. '''
        return self.respbody[:_length]


class _HTTPConnection(object):

    ''' Class corresponding to httplib HTTPConnection class. '''

    def __init__(self, host, cert_file=None, key_file=None, protocol='http'):
        ''' initialize the IWinHttpWebRequest Com Object.'''
        self.host = unicode(host)
        self.cert_file = cert_file
        self._httprequest = _WinHttpRequest()
        self.protocol = protocol
        clsid = GUID('{2087C2F4-2CEF-4953-A8AB-66779B670495}')
        iid = GUID('{016FE2EC-B2C8-45F8-B23B-39E53A75396B}')
        _CoInitialize(None)
        _CoCreateInstance(byref(clsid), 0, 1, byref(iid),
                          byref(self._httprequest))

    def close(self):
        pass

    def set_tunnel(self, host, port=None, headers=None):
        ''' Sets up the host and the port for the HTTP CONNECT Tunnelling. '''
        self._httprequest.set_tunnel(unicode(host), unicode(str(port)))

    def set_proxy_credentials(self, user, password):
        self._httprequest.set_proxy_credentials(
            unicode(user), unicode(password))

    def putrequest(self, method, uri):
        ''' Connects to host and sends the request. '''

        protocol = unicode(self.protocol + '://')
        url = protocol + self.host + unicode(uri)
        self._httprequest.open(unicode(method), url)

        # sets certificate for the connection if cert_file is set.
        if self.cert_file is not None:
            self._httprequest.set_client_certificate(unicode(self.cert_file))

    def putheader(self, name, value):
        ''' Sends the headers of request. '''
        if sys.version_info < (3,):
            name = str(name).decode('utf-8')
            value = str(value).decode('utf-8')
        self._httprequest.set_request_header(name, value)

    def endheaders(self):
        ''' No operation. Exists only to provide the same interface of httplib
        HTTPConnection.'''
        pass

    def send(self, request_body):
        ''' Sends request body. '''
        if not request_body:
            self._httprequest.send()
        else:
            self._httprequest.send(request_body)

    def getresponse(self):
        ''' Gets the response and generates the _Response object'''
        status = self._httprequest.status()
        status_text = self._httprequest.status_text()

        resp_headers = self._httprequest.get_all_response_headers()
        fixed_headers = []
        for resp_header in resp_headers.split('\n'):
            if (resp_header.startswith('\t') or\
                resp_header.startswith(' ')) and fixed_headers:
                # append to previous header
                fixed_headers[-1] += resp_header
            else:
                fixed_headers.append(resp_header)

        headers = []
        for resp_header in fixed_headers:
            if ':' in resp_header:
                pos = resp_header.find(':')
                headers.append(
                    (resp_header[:pos].lower(), resp_header[pos + 1:].strip()))

        body = self._httprequest.response_body()
        length = len(body)

        return _Response(status, status_text, length, headers, body)
