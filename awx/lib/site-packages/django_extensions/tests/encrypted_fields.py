from django.db import connection
from django.conf import settings
from django.core.management import call_command
from django.db.models import loading
from django.utils import unittest

# Only perform encrypted fields tests if keyczar is present
# Resolves http://github.com/django-extensions/django-extensions/issues/#issue/17
try:
    from keyczar import keyczar, keyczart, keyinfo  # NOQA
    from django_extensions.tests.models import Secret
    from django_extensions.db.fields.encrypted import EncryptedTextField, EncryptedCharField  # NOQA
    keyczar_active = hasattr(settings, "ENCRYPTED_FIELD_KEYS_DIR")
except ImportError:
    keyczar_active = False


class EncryptedFieldsTestCase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        if keyczar_active:
            self.crypt = keyczar.Crypter.Read(settings.ENCRYPTED_FIELD_KEYS_DIR)
        super(EncryptedFieldsTestCase, self).__init__(*args, **kwargs)

    def setUp(self):
        self.old_installed_apps = settings.INSTALLED_APPS
        settings.INSTALLED_APPS = list(settings.INSTALLED_APPS)
        settings.INSTALLED_APPS.append('django_extensions.tests')
        loading.cache.loaded = False
        call_command('syncdb', verbosity=0)

    def tearDown(self):
        settings.INSTALLED_APPS = self.old_installed_apps

    def testCharFieldCreate(self):
        if not keyczar_active:
            return
        test_val = "Test Secret"
        secret = Secret.objects.create(name=test_val)
        cursor = connection.cursor()
        query = "SELECT name FROM %s WHERE id = %d" % (Secret._meta.db_table, secret.id)
        cursor.execute(query)
        db_val, = cursor.fetchone()
        decrypted_val = self.crypt.Decrypt(db_val[len(EncryptedCharField.prefix):])
        self.assertEqual(test_val, decrypted_val)

    def testCharFieldRead(self):
        if not keyczar_active:
            return
        test_val = "Test Secret"
        secret = Secret.objects.create(name=test_val)
        retrieved_secret = Secret.objects.get(id=secret.id)
        self.assertEqual(test_val, retrieved_secret.name)

    def testTextFieldCreate(self):
        if not keyczar_active:
            return
        test_val = "Test Secret"
        secret = Secret.objects.create(text=test_val)
        cursor = connection.cursor()
        query = "SELECT text FROM %s WHERE id = %d" % (Secret._meta.db_table, secret.id)
        cursor.execute(query)
        db_val, = cursor.fetchone()
        decrypted_val = self.crypt.Decrypt(db_val[len(EncryptedCharField.prefix):])
        self.assertEqual(test_val, decrypted_val)

    def testTextFieldRead(self):
        if not keyczar_active:
            return
        test_val = "Test Secret"
        secret = Secret.objects.create(text=test_val)
        retrieved_secret = Secret.objects.get(id=secret.id)
        self.assertEqual(test_val, retrieved_secret.text)

