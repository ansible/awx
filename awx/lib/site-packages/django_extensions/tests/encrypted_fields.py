from contextlib import contextmanager
import functools

from django.conf import settings
from django.db import connection, models
from django.db.models import loading

from django_extensions.tests.models import Secret
from django_extensions.tests.fields import FieldTestCase

# Only perform encrypted fields tests if keyczar is present. Resolves
# http://github.com/django-extensions/django-extensions/issues/#issue/17
try:
    from django_extensions.db.fields.encrypted import EncryptedTextField, EncryptedCharField  # NOQA
    from keyczar import keyczar, keyczart, keyinfo  # NOQA
    keyczar_active = True
except ImportError:
    keyczar_active = False


def run_if_active(func):
    "Method decorator that only runs a test if KeyCzar is available."

    @functools.wraps(func)
    def inner(self):
        if not keyczar_active:
            return
        return func(self)
    return inner


# Locations of both private and public keys.
KEY_LOCS = getattr(settings, 'ENCRYPTED_FIELD_KEYS_DIR', {})


@contextmanager
def keys(purpose, mode=None):
    """
    A context manager that sets up the correct KeyCzar environment for a test.

    Arguments:
        purpose: Either keyczar.keyinfo.DECRYPT_AND_ENCRYPT or
                 keyczar.keyinfo.ENCRYPT.
        mode: If truthy, settings.ENCRYPTED_FIELD_MODE will be set to (and then
              reverted from) this value. If falsy, settings.ENCRYPTED_FIELD_MODE
              will not be changed. Optional. Default: None.

    Yields:
        A Keyczar subclass for the stated purpose. This will be keyczar.Crypter
        for DECRYPT_AND_ENCRYPT or keyczar.Encrypter for ENCRYPT. In addition,
        settings.ENCRYPTED_FIELD_KEYS_DIR will be set correctly, and then
        reverted when the manager exits.
    """
    # Store the original settings so we can restore when the manager exits.
    orig_setting_dir = getattr(settings, 'ENCRYPTED_FIELD_KEYS_DIR', None)
    orig_setting_mode = getattr(settings, 'ENCRYPTED_FIELD_MODE', None)
    try:
        if mode:
            settings.ENCRYPTED_FIELD_MODE = mode

        if purpose == keyinfo.DECRYPT_AND_ENCRYPT:
            settings.ENCRYPTED_FIELD_KEYS_DIR = KEY_LOCS['DECRYPT_AND_ENCRYPT']
            yield keyczar.Crypter.Read(settings.ENCRYPTED_FIELD_KEYS_DIR)
        else:
            settings.ENCRYPTED_FIELD_KEYS_DIR = KEY_LOCS['ENCRYPT']
            yield keyczar.Encrypter.Read(settings.ENCRYPTED_FIELD_KEYS_DIR)

    except:
        raise  # Reraise any exceptions.

    finally:
        # Restore settings.
        settings.ENCRYPTED_FIELD_KEYS_DIR = orig_setting_dir
        if mode:
            if orig_setting_mode:
                settings.ENCRYPTED_FIELD_MODE = orig_setting_mode
            else:
                del settings.ENCRYPTED_FIELD_MODE


@contextmanager
def secret_model():
    """
    A context manager that yields a Secret model defined at runtime.

    All EncryptedField init logic occurs at model class definition time, not at
    object instantiation time. This means that in order to test different keys
    and modes, we must generate a new class definition at runtime, after
    establishing the correct KeyCzar settings. This context manager handles
    that process.

    See http://dynamic-models.readthedocs.org/en/latest/ and
    https://docs.djangoproject.com/en/dev/topics/db/models/
        #differences-between-proxy-inheritance-and-unmanaged-models
    """

    # Store Django's cached model, if present, so we can restore when the
    # manager exits.
    orig_model = None
    try:
        orig_model = loading.cache.app_models['tests']['secret']
        del loading.cache.app_models['tests']['secret']
    except KeyError:
        pass

    try:
        # Create a new class that shadows tests.models.Secret.
        attrs = {
            'name': EncryptedCharField("Name", max_length=Secret._meta.get_field('name').max_length),
            'text': EncryptedTextField("Text"),
            '__module__': 'django_extensions.tests.models',
            'Meta': type('Meta', (object, ), {
                'managed': False,
                'db_table': Secret._meta.db_table
            })
        }
        yield type('Secret', (models.Model, ), attrs)

    except:
        raise  # Reraise any exceptions.

    finally:
        # Restore Django's model cache.
        try:
            loading.cache.app_models['tests']['secret'] = orig_model
        except KeyError:
            pass


class EncryptedFieldsTestCase(FieldTestCase):
    @run_if_active
    def testCharFieldCreate(self):
        """
        Uses a private key to encrypt data on model creation.
        Verifies the data is encrypted in the database and can be decrypted.
        """
        with keys(keyinfo.DECRYPT_AND_ENCRYPT) as crypt:
            with secret_model() as model:
                test_val = "Test Secret"
                secret = model.objects.create(name=test_val)

                cursor = connection.cursor()
                query = "SELECT name FROM %s WHERE id = %d" % (model._meta.db_table, secret.id)
                cursor.execute(query)
                db_val, = cursor.fetchone()
                decrypted_val = crypt.Decrypt(db_val[len(EncryptedCharField.prefix):])
                self.assertEqual(test_val, decrypted_val)

    @run_if_active
    def testCharFieldRead(self):
        """
        Uses a private key to encrypt data on model creation.
        Verifies the data is decrypted when reading the value back from the
        model.
        """
        with keys(keyinfo.DECRYPT_AND_ENCRYPT):
            with secret_model() as model:
                test_val = "Test Secret"
                secret = model.objects.create(name=test_val)
                retrieved_secret = model.objects.get(id=secret.id)
                self.assertEqual(test_val, retrieved_secret.name)

    @run_if_active
    def testTextFieldCreate(self):
        """
        Uses a private key to encrypt data on model creation.
        Verifies the data is encrypted in the database and can be decrypted.
        """
        with keys(keyinfo.DECRYPT_AND_ENCRYPT) as crypt:
            with secret_model() as model:
                test_val = "Test Secret"
                secret = model.objects.create(text=test_val)
                cursor = connection.cursor()
                query = "SELECT text FROM %s WHERE id = %d" % (model._meta.db_table, secret.id)
                cursor.execute(query)
                db_val, = cursor.fetchone()
                decrypted_val = crypt.Decrypt(db_val[len(EncryptedCharField.prefix):])
                self.assertEqual(test_val, decrypted_val)

    @run_if_active
    def testTextFieldRead(self):
        """
        Uses a private key to encrypt data on model creation.
        Verifies the data is decrypted when reading the value back from the
        model.
        """
        with keys(keyinfo.DECRYPT_AND_ENCRYPT):
            with secret_model() as model:
                test_val = "Test Secret"
                secret = model.objects.create(text=test_val)
                retrieved_secret = model.objects.get(id=secret.id)
                self.assertEqual(test_val, retrieved_secret.text)

    @run_if_active
    def testCannotDecrypt(self):
        """
        Uses a public key to encrypt data on model creation.
        Verifies that the data cannot be decrypted using the same key.
        """
        with keys(keyinfo.ENCRYPT, mode=keyinfo.ENCRYPT.name):
            with secret_model() as model:
                test_val = "Test Secret"
                secret = model.objects.create(name=test_val)
                retrieved_secret = model.objects.get(id=secret.id)
                self.assertNotEqual(test_val, retrieved_secret.name)
                self.assertTrue(retrieved_secret.name.startswith(EncryptedCharField.prefix))

    @run_if_active
    def testUnacceptablePurpose(self):
        """
        Tries to create an encrypted field with a mode mismatch.
        A purpose of "DECRYPT_AND_ENCRYPT" cannot be used with a public key,
        since public keys cannot be used for decryption. This should raise an
        exception.
        """
        with self.assertRaises(keyczar.errors.KeyczarError):
            with keys(keyinfo.ENCRYPT):
                with secret_model():
                    # A KeyCzar exception should get raised during class
                    # definition time, so any code in here would never get run.
                    pass

    @run_if_active
    def testDecryptionForbidden(self):
        """
        Uses a private key to encrypt data, but decryption is not allowed.
        ENCRYPTED_FIELD_MODE is explicitly set to ENCRYPT, meaning data should
        not be decrypted, even though the key would allow for it.
        """
        with keys(keyinfo.DECRYPT_AND_ENCRYPT, mode=keyinfo.ENCRYPT.name):
            with secret_model() as model:
                test_val = "Test Secret"
                secret = model.objects.create(name=test_val)
                retrieved_secret = model.objects.get(id=secret.id)
                self.assertNotEqual(test_val, retrieved_secret.name)
                self.assertTrue(retrieved_secret.name.startswith(EncryptedCharField.prefix))

    @run_if_active
    def testEncryptPublicDecryptPrivate(self):
        """
        Uses a public key to encrypt, and a private key to decrypt data.
        """
        test_val = "Test Secret"

        # First, encrypt data with public key and save to db.
        with keys(keyinfo.ENCRYPT, mode=keyinfo.ENCRYPT.name):
            with secret_model() as model:
                secret = model.objects.create(name=test_val)
                enc_retrieved_secret = model.objects.get(id=secret.id)
                self.assertNotEqual(test_val, enc_retrieved_secret.name)
                self.assertTrue(enc_retrieved_secret.name.startswith(EncryptedCharField.prefix))

        # Next, retrieve data from db, and decrypt with private key.
        with keys(keyinfo.DECRYPT_AND_ENCRYPT):
            with secret_model() as model:
                retrieved_secret = model.objects.get(id=secret.id)
                self.assertEqual(test_val, retrieved_secret.name)

