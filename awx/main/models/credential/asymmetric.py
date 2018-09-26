# REST Framework - used manually for generator kwargs validation
from rest_framework import serializers as drf_serializers
from rest_framework.fields import empty

# python cryptography hazardous materials
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


class AsymmetricFieldBase(object):
    credential_type = None
    input_field = None
    generate_fields = ()

    def validate_generator_kwargs(self, kwargs):
        ret = {}
        for key, field in self.generate_fields.items():
            if field in kwargs:
                field.run_validation(kwargs[key])
                ret[key] = kwargs[key]
            elif field.default is not empty:
                ret[key] = field.default
        return ret


class MachineRSA(AsymmetricFieldBase):
    credential_type = 'Machine'
    input_field = 'ssh_key_data'
    generate_fields = {
        'public_exponent': drf_serializers.IntegerField(max_value=None, min_value=1, default=65537),
        'key_size': drf_serializers.IntegerField(max_value=None, min_value=512, default=4096),
        'key_unlock': drf_serializers.CharField()
    }

    def generate_private_key(self, public_exponent, key_size, key_unlock=None):
        if not key_unlock:
            encrypter = serialization.NoEncryption()
        else:
            encrypter = serialization.BestAvailableEncryption(key_unlock)
        private_key = rsa.generate_private_key(
            public_exponent=public_exponent,
            key_size=key_size,
            backend=default_backend()
        )
        return private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            encrypter
        )

    def get_public_data(self, private_data, key_unlock=None):
        private_key = serialization.load_pem_private_key(
            str(private_data),
            password=key_unlock,
            backend=default_backend()
        )
        return private_key.public_key().public_bytes(
            serialization.Encoding.OpenSSH,
            serialization.PublicFormat.OpenSSH
        )

    def generate(self, inputs):
        kwargs = inputs.get('ssh_key_data').get('$generate$')
        key_unlock = inputs.get('ssh_key_unlock')
        if key_unlock:
            kwargs['key_unlock'] = key_unlock
        kwargs = self.validate_generator_kwargs(kwargs)
        return self.generate_private_key(**kwargs)


def get_type_data_mangers(ct):
    r = {}
    for cls in AsymmetricFieldBase.__subclasses__():
        if cls.credential_type == ct.name:
            r[cls.input_field] = cls()
    return r
