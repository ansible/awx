from __future__ import absolute_import

import os
import sys
import copy
import codecs
import cPickle
import base64
import io

try:
    import gdata.docs.service
except ImportError:
    pass

from . import keyczar
from keyring import errors
from keyring import credentials
import keyring.py27compat
from keyring.backend import KeyringBackend
from keyring.util import properties
from keyring.errors import ExceptionRaisedContext

class EnvironCredential(credentials.EnvironCredential):
    """Retrieve credentials from specifically named environment variables
    """

    def __init__(self):
        super(EnvironCredential, self).__init__('GOOGLE_KEYRING_USER',
            'GOOGLE_KEYRING_PASSWORD')

class DocsKeyring(KeyringBackend):
    """Backend that stores keyring on Google Docs.
       Note that login and any other initialisation is deferred until it is
       actually required to allow this keyring class to be added to the
       global _all_keyring list.
    """

    keyring_title = 'GoogleKeyring'
    # status enums
    OK = 1
    FAIL = 0
    CONFLICT = -1

    def __init__(self, credential, source, crypter,
                 collection=None, client=None,
                 can_create=True, input_getter=keyring.py27compat.input
                ):
        self.credential = credential
        self.crypter = crypter
        self.source = source
        self._collection = collection
        self.can_create = can_create
        self.input_getter = input_getter
        self._keyring_dict = None

        if not client:
            self._client = gdata.docs.service.DocsService()
        else:
            self._client = client

        self._client.source = source
        self._client.ssl = True
        self._login_reqd = True

    @properties.ClassProperty
    @classmethod
    def priority(cls):
        if not cls._has_gdata():
            raise RuntimeError("Requires gdata")
        if not keyczar.has_keyczar():
            raise RuntimeError("Requires keyczar")
        return 3

    @classmethod
    def _has_gdata(cls):
        with ExceptionRaisedContext() as exc:
            gdata.__name__
        return not bool(exc)

    def get_password(self, service, username):
        """Get password of the username for the service
        """
        result = self._get_entry(self._keyring, service, username)
        if result:
            result = self._decrypt(result)
        return result

    def set_password(self, service, username, password):
        """Set password for the username of the service
        """
        password = self._encrypt(password or '')
        keyring_working_copy = copy.deepcopy(self._keyring)
        service_entries = keyring_working_copy.get(service)
        if not service_entries:
            service_entries = {}
            keyring_working_copy[service] = service_entries
        service_entries[username] = password
        save_result = self._save_keyring(keyring_working_copy)
        if save_result == self.OK:
            self._keyring_dict = keyring_working_copy
            return
        elif save_result == self.CONFLICT:
            # check if we can avoid updating
            self.docs_entry, keyring_dict = self._read()
            existing_pwd = self._get_entry(self._keyring, service, username)
            conflicting_pwd = self._get_entry(keyring_dict, service, username)
            if conflicting_pwd == password:
                # if someone else updated it to the same value then we are done
                self._keyring_dict = keyring_working_copy
                return
            elif conflicting_pwd is None or conflicting_pwd == existing_pwd:
                # if doesn't already exist or is unchanged then update it
                new_service_entries = keyring_dict.get(service, {})
                new_service_entries[username] = password
                keyring_dict[service] = new_service_entries
                save_result = self._save_keyring(keyring_dict)
                if save_result == self.OK:
                    self._keyring_dict = keyring_dict
                    return
                else:
                    raise errors.PasswordSetError(
                        'Failed write after conflict detected')
            else:
                raise errors.PasswordSetError(
                    'Conflict detected, service:%s and username:%s was '\
                    'set to a different value by someone else' %(service,
                                                                 username))

        raise errors.PasswordSetError('Could not save keyring')

    def delete_password(self, service, username):
        return self._del_entry(self._keyring, service, username)

    @property
    def client(self):
        if not self._client.GetClientLoginToken():
            try:
                self._client.ClientLogin(self.credential.username,
                                         self.credential.password,
                                         self._client.source)
            except gdata.service.CaptchaRequired:
                sys.stdout.write('Please visit ' + self._client.captcha_url)
                answer = self.input_getter('Answer to the challenge? ')
                self._client.email = self.credential.username
                self._client.password = self.credential.password
                self._client.ClientLogin(
                    self.credential.username,
                    self.credential.password,
                    self._client.source,
                    captcha_token=self._client.captcha_token,
                    captcha_response=answer)
            except gdata.service.BadAuthentication:
                raise errors.InitError('Users credential were unrecognized')
            except gdata.service.Error:
                raise errors.InitError('Login Error')

        return self._client

    @property
    def collection(self):
        return self._collection or self.credential.username.split('@')[0]

    @property
    def _keyring(self):
        if self._keyring_dict is None:
            self.docs_entry, self._keyring_dict = self._read()
        return self._keyring_dict

    def _get_entry(self, keyring_dict, service, username):
        result = None
        service_entries = keyring_dict.get(service)
        if service_entries:
            result = service_entries.get(username)
        return result

    def _del_entry(self, keyring_dict, service, username):
        service_entries = keyring_dict.get(service)
        if not service_entries:
            raise errors.PasswordDeleteError("No matching service")
        try:
            del service_entries[username]
        except KeyError:
            raise errors.PasswordDeleteError("Not found")
        if not service_entries:
            del keyring_dict[service]

    def _decrypt(self, value):
        if not value:
            return ''
        return self.crypter.decrypt(value)

    def _encrypt(self, value):
        if not value:
            return ''
        return self.crypter.encrypt(value)

    def _get_doc_title(self):
        return '%s' %self.keyring_title

    def _read(self):
        from gdata.docs.service import DocumentQuery
        import gdata
        title_query = DocumentQuery(categories=[self.collection])
        title_query['title'] = self._get_doc_title()
        title_query['title-exact'] = 'true'
        docs = self.client.QueryDocumentListFeed(title_query.ToUri())

        if not docs.entry:
            if self.can_create:
                docs_entry = None
                keyring_dict = {}
            else:
                raise errors.InitError(
                    '%s not found in %s and create not permitted'
                    %(self._get_doc_title(), self.collection))
        else:
            docs_entry = docs.entry[0]
            file_contents = ''
            try:
                url = docs_entry.content.src
                url += '&exportFormat=txt'
                server_response = self.client.request('GET', url)
                if server_response.status != 200:
                    raise errors.InitError(
                        'Could not read existing Google Docs keyring')
                file_contents = server_response.read()
                if file_contents.startswith(codecs.BOM_UTF8):
                    file_contents = file_contents[len(codecs.BOM_UTF8):]
                keyring_dict = cPickle.loads(base64.urlsafe_b64decode(
                    file_contents.decode('string-escape')))
            except cPickle.UnpicklingError, ex:
                raise errors.InitError(
                    'Could not unpickle existing Google Docs keyring', ex)
            except TypeError, ex:
                raise errors.InitError(
                    'Could not decode existing Google Docs keyring', ex)

        return docs_entry, keyring_dict

    def _save_keyring(self, keyring_dict):
        """Helper to actually write the keyring to Google"""
        import gdata
        result = self.OK
        file_contents = base64.urlsafe_b64encode(cPickle.dumps(keyring_dict))
        try:
            if self.docs_entry:
                extra_headers = {'Content-Type': 'text/plain',
                                 'Content-Length': len(file_contents)}
                self.docs_entry = self.client.Put(
                    file_contents,
                    self.docs_entry.GetEditMediaLink().href,
                    extra_headers=extra_headers
                    )
            else:
                from gdata.docs.service import DocumentQuery
                # check for existence of folder, create if required
                folder_query = DocumentQuery(categories=['folder'])
                folder_query['title'] = self.collection
                folder_query['title-exact'] = 'true'
                docs = self.client.QueryDocumentListFeed(folder_query.ToUri())
                if docs.entry:
                    folder_entry = docs.entry[0]
                else:
                    folder_entry = self.client.CreateFolder(self.collection)
                file_handle = io.BytesIO(file_contents)
                media_source = gdata.MediaSource(
                    file_handle=file_handle,
                    content_type='text/plain',
                    content_length=len(file_contents),
                    file_name='temp')
                self.docs_entry = self.client.Upload(
                    media_source,
                    self._get_doc_title(),
                    folder_or_uri=folder_entry
                )
        except gdata.service.RequestError, ex:
            try:
                if ex.message['reason'].lower().find('conflict') != -1:
                    result = self.CONFLICT
                else:
                    # Google docs has a bug when updating a shared document
                    # using PUT from any account other that the owner.
                    # It returns an error 400 "Sorry, there was an error saving the file. Please try again"
                    # *despite* actually updating the document!
                    # Workaround by re-reading to see if it actually updated
                    if ex.message['body'].find(
                        'Sorry, there was an error saving the file') != -1:
                        new_docs_entry, new_keyring_dict = self._read()
                        if new_keyring_dict == keyring_dict:
                            result = self.OK
                        else:
                            result = self.FAIL
                    else:
                        result = self.FAIL
            except:
                result = self.FAIL

        return result

class KeyczarDocsKeyring(DocsKeyring):
    """Google Docs keyring using keyczar initialized from environment
    variables
    """

    def __init__(self):
        crypter = keyczar.EnvironCrypter()
        credential = EnvironCredential()
        source = os.environ.get('GOOGLE_KEYRING_SOURCE')
        super(KeyczarDocsKeyring, self).__init__(
            credential, source, crypter)

    def supported(self):
        """Return if this keyring supports current environment:
        -1: not applicable
         0: suitable
         1: recommended
        """
        try:
            from keyczar import keyczar
            return super(KeyczarDocsKeyring, self).supported()
        except ImportError:
            return -1
