import codecs
import base64

from ..py30compat import unittest
from ..test_backend import BackendBasicTests
from keyring.backends import Google
from keyring.credentials import SimpleCredential
from keyring.backend import NullCrypter
from keyring import errors
from keyring.py27compat import input, pickle
from .. import mocks

def is_gdata_supported():
    try:
        __import__('gdata.service')
    except ImportError:
        return False
    return True

def init_google_docs_keyring(client, can_create=True,
                             input_getter=input):
    credentials = SimpleCredential('foo', 'bar')
    return Google.DocsKeyring(credentials,
                                             'test_src',
                                             NullCrypter(),
                                             client=client,
                                             can_create=can_create,
                                             input_getter=input_getter
                                            )

@unittest.skipUnless(is_gdata_supported(),
                     "Need Google Docs (gdata)")
class GoogleDocsKeyringTestCase(BackendBasicTests, unittest.TestCase):
    """Run all the standard tests on a new keyring"""

    def init_keyring(self):
        client = mocks.MockDocumentService()
        client.SetClientLoginToken('foo')
        return init_google_docs_keyring(client)

@unittest.skipUnless(is_gdata_supported(),
                     "Need Google Docs (gdata)")
class GoogleDocsKeyringInteractionTestCase(unittest.TestCase):
    """Additional tests for Google Doc interactions"""

    def _init_client(self, set_token=True):
        client = mocks.MockDocumentService()
        if set_token:
            client.SetClientLoginToken('interaction')
        return client

    def _init_keyring(self, client):
        self.keyring = init_google_docs_keyring(client)

    def _init_listfeed(self):
        listfeed = mocks.MockListFeed()
        listfeed._entry = [mocks.MockDocumentListEntry(),
                           mocks.MockDocumentListEntry()
                          ]
        return listfeed

    def _encode_data(self, data):
        return base64.urlsafe_b64encode(pickle.dumps(data))

    def test_handles_auth_failure(self):
        import gdata
        client = self._init_client(set_token=False)
        client._login_err = gdata.service.BadAuthentication
        self._init_keyring(client)
        with self.assertRaises(errors.InitError):
            self.keyring.client

    def test_handles_auth_error(self):
        import gdata
        client = self._init_client(set_token=False)
        client._login_err = gdata.service.Error
        self._init_keyring(client)
        with self.assertRaises(errors.InitError):
            self.keyring.client

    def test_handles_login_captcha(self):
        import gdata
        client = self._init_client(set_token=False)
        client._login_err = gdata.service.CaptchaRequired
        client.captcha_url = 'a_captcha_url'
        client.captcha_token = 'token'
        self.get_input_called = False
        def _get_input(prompt):
            self.get_input_called = True
            delattr(client, '_login_err')
            return 'Foo'
        self.keyring = init_google_docs_keyring(client, input_getter=_get_input)
        self.keyring.client
        self.assertTrue(self.get_input_called, 'Should have got input')

    def test_retrieves_existing_keyring_with_and_without_bom(self):
        client = self._init_client()
        dummy_entries = dict(section1=dict(user1='pwd1'))
        no_utf8_bom_entries = self._encode_data(dummy_entries)
        client._request_response = dict(status=200, data=no_utf8_bom_entries)
        client._listfeed = self._init_listfeed()
        self._init_keyring(client)
        self.assertEqual(self.keyring.get_password('section1', 'user1'), 'pwd1')

        utf8_bom_entries = codecs.BOM_UTF8 + no_utf8_bom_entries
        client._request_response = dict(status=200, data=utf8_bom_entries)
        self._init_keyring(client)
        self.assertEqual(self.keyring.get_password('section1', 'user1'), 'pwd1')

    def test_handles_retrieve_failure(self):
        client = self._init_client()
        client._listfeed = self._init_listfeed()
        client._request_response = dict(status=400,
                                        reason='Data centre explosion')
        self._init_keyring(client)
        self.assertRaises(errors.InitError, self.keyring.get_password, 'any', 'thing')

    def test_handles_corrupt_retrieve(self):
        client = self._init_client()
        dummy_entries = dict(section1=dict(user1='pwd1'))
        client._request_response = dict(status=200, data='broken' + self._encode_data(dummy_entries))
        client._listfeed = self._init_listfeed()
        self._init_keyring(client)
        self.assertRaises(errors.InitError, self.keyring.get_password, 'any', 'thing')

    def test_no_create_if_requested(self):
        client = self._init_client()
        self.keyring = init_google_docs_keyring(client, can_create=False)
        self.assertRaises(errors.InitError, self.keyring.get_password, 'any', 'thing')

    def test_no_set_if_create_folder_fails_on_new_keyring(self):
        import gdata
        client = self._init_client()
        client._create_folder_err = gdata.service.RequestError
        self._init_keyring(client)
        self.assertEqual(self.keyring.get_password('service-a', 'user-A'), None,
                        'No password should be set in new keyring')
        self.assertRaises(errors.PasswordSetError, self.keyring.set_password,
                          'service-a', 'user-A', 'password-A')
        self.assertEqual(self.keyring.get_password('service-a', 'user-A'), None,
                        'No password should be set after write fail')

    def test_no_set_if_write_fails_on_new_keyring(self):
        import gdata
        client = self._init_client()
        client._upload_err = gdata.service.RequestError
        self._init_keyring(client)
        self.assertEqual(self.keyring.get_password('service-a', 'user-A'), None,
                        'No password should be set in new keyring')
        self.assertRaises(errors.PasswordSetError, self.keyring.set_password,
                          'service-a', 'user-A', 'password-A')
        self.assertEqual(self.keyring.get_password('service-a', 'user-A'), None,
                        'No password should be set after write fail')

    def test_no_set_if_write_fails_on_existing_keyring(self):
        import gdata
        client = self._init_client()
        dummy_entries = dict(sectionB=dict(user9='pwd9'))
        client._request_response = dict(status=200, data=self._encode_data(dummy_entries))
        client._put_err = gdata.service.RequestError
        client._listfeed = self._init_listfeed()
        self._init_keyring(client)
        self.assertEqual(self.keyring.get_password('sectionB', 'user9'), 'pwd9',
                        'Correct password should be set in existing keyring')
        self.assertRaises(errors.PasswordSetError, self.keyring.set_password,
                          'sectionB', 'user9', 'Not the same pwd')
        self.assertEqual(self.keyring.get_password('sectionB', 'user9'), 'pwd9',
                        'Password should be unchanged after write fail')

    def test_writes_correct_data_to_google_docs(self):
        client = self._init_client()
        dummy_entries = dict(sectionWriteChk=dict(userWriteChk='pwd'))
        client._request_response = dict(status=200, data=self._encode_data(dummy_entries))
        client._listfeed = self._init_listfeed()
        self._init_keyring(client)
        self.keyring.set_password('sectionWriteChk',
                                  'userWritechk',
                                  'new_pwd')
        self.assertIsNotNone(client._put_data, 'Should have written data')
        self.assertEquals(
            'new_pwd',
            client._put_data.get('sectionWriteChk').get('userWritechk'),
            'Did not write updated password!')

    def test_handles_write_conflict_on_different_service(self):
        import gdata
        client = self._init_client()
        dummy_entries = dict(sectionWriteConflictA=dict(
            userwriteConflictA='pwdwriteConflictA'))
        client._request_response = dict(status=200, data=self._encode_data(dummy_entries))
        client._put_err = [(gdata.service.RequestError,
                               {'status': '406',
                                'reason': 'Conflict'}),]
        client._listfeed = self._init_listfeed()
        self._init_keyring(client)
        self.assertEqual(
            self.keyring.get_password('sectionWriteConflictA',
                                      'userwriteConflictA'),
            'pwdwriteConflictA',
            'Correct password should be set in existing keyring')
        dummy_entries['diffSection'] = dict(foo='bar')
        client._request_response = dict(status=200, data=self._encode_data(dummy_entries))
        new_pwd = 'Not the same pwd'
        self.keyring.set_password('sectionWriteConflictA',
                                  'userwriteConflictA',
                                  new_pwd)

        self.assertEquals(self.keyring.get_password('sectionWriteConflictA',
                                                    'userwriteConflictA'),
                          new_pwd
        )
        self.assertEqual(1, client._put_count,
                         'Write not called after conflict resolution')

    def test_handles_write_conflict_on_same_service_and_username(self):
        import gdata
        client = self._init_client()
        dummy_entries = dict(sectionWriteConflictB=dict(
            userwriteConflictB='pwdwriteConflictB'))
        client._request_response = dict(status=200, data=self._encode_data(dummy_entries))
        client._put_err = (gdata.service.RequestError,
                               {'status': '406',
                                'reason': 'Conflict'})
        client._listfeed = self._init_listfeed()
        self._init_keyring(client)
        self.assertEqual(
            self.keyring.get_password('sectionWriteConflictB',
                                      'userwriteConflictB'),
            'pwdwriteConflictB',
            'Correct password should be set in existing keyring')
        conflicting_dummy_entries = dict(sectionWriteConflictB=dict(
            userwriteConflictB='pwdwriteConflictC'))
        client._request_response = dict(status=200, data=self._encode_data(conflicting_dummy_entries))
        self.assertRaises(errors.PasswordSetError, self.keyring.set_password,
                          'sectionWriteConflictB', 'userwriteConflictB', 'new_pwd')

    def test_handles_write_conflict_with_identical_change(self):
        import gdata
        client = self._init_client()
        dummy_entries = dict(sectionWriteConflictC=dict(
            userwriteConflictC='pwdwriteConflictC'))
        client._request_response = dict(status=200, data=self._encode_data(dummy_entries))
        client._put_err = [(gdata.service.RequestError,
                               {'status': '406',
                                 'reason': 'Conflict'}),]
        client._listfeed = self._init_listfeed()
        self._init_keyring(client)
        self.assertEqual(
            self.keyring.get_password('sectionWriteConflictC',
                                      'userwriteConflictC'),
            'pwdwriteConflictC',
            'Correct password should be set in existing keyring')
        new_pwd = 'Not the same pwd'
        conflicting_dummy_entries = dict(sectionWriteConflictC=dict(
            userwriteConflictC=new_pwd))
        client._request_response = dict(status=200, data=self._encode_data(conflicting_dummy_entries))
        self.keyring.set_password('sectionWriteConflictC',
                                  'userwriteConflictC',
                                  new_pwd)
        self.assertEquals(self.keyring.get_password('sectionWriteConflictC',
                                                    'userwriteConflictC'),
                          new_pwd
        )

    def test_handles_broken_google_put_when_non_owner_update_fails(self):
        """Google Docs has a bug when putting to a non-owner
           see  GoogleDocsKeyring._save_keyring()
        """
        import gdata
        client = self._init_client()
        dummy_entries = dict(sectionBrokenPut=dict(
            userBrokenPut='pwdBrokenPut'))
        client._request_response = dict(status=200, data=self._encode_data(dummy_entries))
        client._put_err = [(
            gdata.service.RequestError,
                { 'status': '400',
                  'body': 'Sorry, there was an error saving the file. Please try again.',
                  'reason': 'Bad Request'}),]
        client._listfeed = self._init_listfeed()
        self._init_keyring(client)
        new_pwd = 'newPwdBrokenPut'
        correct_read_entries = dict(sectionBrokenPut=dict(
            userBrokenPut='pwdBrokenPut'))
        client._request_response = dict(status=200,
                                        data=self._encode_data(correct_read_entries))
        self.assertRaises(errors.PasswordSetError, self.keyring.set_password,
                          'sectionBrokenPut', 'userBrokenPut', new_pwd)

    def test_handles_broken_google_put_when_non_owner_update(self):
        """Google Docs has a bug when putting to a non-owner
           see  GoogleDocsKeyring._save_keyring()
        """
        import gdata
        client = self._init_client()
        dummy_entries = dict(sectionBrokenPut=dict(
            userBrokenPut='pwdBrokenPut'))
        client._request_response = dict(status=200, data=self._encode_data(dummy_entries))
        client._put_err = [(
            gdata.service.RequestError,
                { 'status': '400',
                  'body': 'Sorry, there was an error saving the file. Please try again.',
                  'reason': 'Bad Request'}),]
        client._listfeed = self._init_listfeed()
        self._init_keyring(client)
        new_pwd = 'newPwdBrokenPut'
        correct_read_entries = dict(sectionBrokenPut=dict(
            userBrokenPut=new_pwd))
        client._request_response = dict(status=200,
                                        data=self._encode_data(correct_read_entries))
        self.keyring.set_password('sectionBrokenPut',
                                  'userBrokenPut',
                                  new_pwd)
        self.assertEquals(self.keyring.get_password('sectionBrokenPut',
                                                    'userBrokenPut'),
                          new_pwd)

    def test_uses_existing_folder(self):
        import gdata
        client = self._init_client()
        # should not happen
        client._create_folder_err = gdata.service.RequestError

        self._init_keyring(client)
        self.assertEqual(self.keyring.get_password('service-a', 'user-A'), None,
                         'No password should be set in new keyring')
        client._listfeed = self._init_listfeed()
        self.keyring.set_password('service-a', 'user-A', 'password-A')
        self.assertIsNotNone(client._upload_data, 'Should have written data')
        self.assertEqual(self.keyring.get_password('service-a', 'user-A'),
                         'password-A',
                         'Correct password should be set')
