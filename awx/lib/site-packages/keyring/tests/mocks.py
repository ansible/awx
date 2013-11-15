"""
mocks.py

Various mock objects for testing
"""

import base64
from keyring.py27compat import pickle, unicode_str
try:
    from StringIO import StringIO
except ImportError: # For Python 3
    from io import StringIO

class MockAtom(object):
    """ Mocks an atom in the GData service. """
    def __init__(self, value):
        self.text = value
        
class MockEntry(object):
    """ Mocks and entry returned from the GData service. """       
    def __init__(self, title, ID):
        self.title = MockAtom(title)
        self.id = MockAtom('http://mock.example.com/%s' % ID)
        self.ID = ID # simpler lookup for key value

    def GetEditMediaLink(self):
        return MockLink()
    

class MockHTTPClient(object):
    """ Mocks the functionality of an http client. """
    def request(*args, **kwargs):
        pass
    
class MockGDataService(object):
    """ Provides the common functionality of a Google Service. """
    http_client = MockHTTPClient()
    def __init__(self, email=None, password=None,
                 account_type='HOSTED_OR_GOOGLE', service=None,
                 auth_service_url=None, source=None, server=None,
                 additional_headers=None, handler=None, tokens=None,
                 http_client=None, token_store=None):
        """ Create the Service with the default parameters. """
        self.email = email
        self.password = password
        self.account_type = account_type
        self.service = service
        self.auth_service_url = auth_service_url
        self.server = server
        self.login_token = None
    
    def GetClientLoginToken(self):
        return self.login_token
        
    def SetClientLoginToken(self, token):
        self.login_token = token
        
    def ClientLogin(self, username, password, account_type=None, service=None,
                    auth_service_url=None, source=None, captcha_token=None, 
                    captcha_response=None):
        
        """ Client side login to the service. """
        if hasattr(self, '_login_err'):
            raise self._login_err()

class MockDocumentService(MockGDataService):
    """ 
    Implements the minimum functionality of the Google Document service. 
    """

    def Upload(self, media_source, title, folder_or_uri=None, label=None):
        """ 
        Upload a document.  
        """
        if hasattr(self, '_upload_err'):
            raise self._upload_err()
        if not hasattr(self, '_upload_count'):
            self._upload_count = 0
        # save the data for asserting against
        self._upload_data =  dict(media_source=media_source, title=title,
                               folder_or_uri=folder_or_uri, label=label)
        self._upload_count += 1
        return MockEntry(title, 'mockentry%3A' + title)
    
    def QueryDocumentListFeed(self, uri):
        if hasattr(self, '_listfeed'):
            return self._listfeed
        return MockListFeed()
                              
    def CreateFolder(self, title, folder_or_uri=None):
        if hasattr(self, '_create_folder_err'):
            raise self._create_folder_err()
        if hasattr(self, '_create_folder'):
            return self._create_folder
        return MockListEntry()

    def Put(self, data, uri, extra_headers=None, url_params=None, 
            escape_params=True, redirects_remaining=3, media_source=None,
            converter=None):
        self._put_data = None
        if not hasattr(self, '_put_count'):
            self._put_count = 0
        if hasattr(self, '_put_err'):
            # allow for a list of errors
            if type(self._put_err) == list:
                put_err = self._put_err.pop(0)
                if not len(self._put_err):
                    delattr(self, '_put_err')
            else:
                put_err = self._put_err
            if type(put_err) == tuple:
                raise put_err[0](put_err[1])
            else:
                raise put_err()
        # save the data for asserting against
        assert isinstance(data, str) or isinstance(data, unicode_str), \
            'Should be a string'
        self._put_data =  pickle.loads(base64.urlsafe_b64decode(data))
        self._put_count += 1
        return MockEntry('', 'mockentry%3A' + '')

    def Export(self, entry_or_id_or_url, file_path, gid=None, extra_params=None):
        if hasattr(self, '_export_err'):
            raise self._export_err()
        if hasattr(self, '_export_data'):
            export_file = open(file_path, 'wb')
            export_file.write(self._export_data)
            export_file.close()

    def request(self, data, uri):
        if hasattr(self, '_request_err'):
            if type(self._request_err) == tuple:
                raise self._request_err[0](self._request_err[1])
            else:
                raise self._request_err()
        if hasattr(self, '_request_response'):
            return MockHttpResponse(self._request_response)

class MockHttpResponse(StringIO, object):

    def __init__(self, response_dict):
        super(MockHttpResponse, self).__init__(response_dict.get('data', ''))
        self.status = response_dict.get('status', 200)
        self.reason = response_dict.get('reason', '')

class MockListFeed(object):

    @property
    def entry(self):
        if hasattr(self, '_entry'):
            return self._entry
        return []

class MockListEntry(object):

    pass

class MockLink(object):

    @property
    def href(self):
        return ''

class MockContent(object):

    @property
    def src(self):
        return 'src'

class MockDocumentListEntry(object):

    @property
    def content(self):
        return MockContent()

    def GetEditMediaLink(self):
        return MockLink()

class MockKeyczarReader(object):

    def __init__(self, location):
        self.location = location

class MockKeyczarEncryptedReader(object):

    def __init__(self, reader, crypter):
        self._reader = reader
        self._crypter = crypter

class MockKeyczarReaders(object):

    @staticmethod
    def CreateReader(location):
        return MockKeyczarReader(location)

    @staticmethod
    def EncryptedReader(reader, crypter):
        return MockKeyczarEncryptedReader(reader, crypter)

class MockKeyczarCrypter(object):

    def __init__(self, reader):
        self.reader = reader

    @staticmethod
    def Read(location):
        return MockKeyczarCrypter(MockKeyczarReader(location))

class MockKeyczar(object):

    @property
    def readers(self):
       return MockKeyczarReaders

    @property
    def Crypter(self):
        return MockKeyczarCrypter
