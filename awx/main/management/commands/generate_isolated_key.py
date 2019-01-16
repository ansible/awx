# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved
import datetime
from django.utils.encoding import smart_str

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.conf import settings
from django.core.management.base import BaseCommand

from awx.conf.models import Setting


class Command(BaseCommand):
    """Generate and store a randomized RSA key for SSH traffic to isolated instances"""
    help = 'Generates and stores a randomized RSA key for SSH traffic to isolated instances'

    def handle(self, *args, **kwargs):
        if getattr(settings, 'AWX_ISOLATED_PRIVATE_KEY', False):
            print(settings.AWX_ISOLATED_PUBLIC_KEY)
            return

        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
            backend=default_backend()
        )
        Setting.objects.create(
            key='AWX_ISOLATED_PRIVATE_KEY',
            value=key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            )
        ).save()
        pemfile = Setting.objects.create(
            key='AWX_ISOLATED_PUBLIC_KEY',
            value=smart_str(key.public_key().public_bytes(
                encoding=serialization.Encoding.OpenSSH,
                format=serialization.PublicFormat.OpenSSH
            )) + " generated-by-awx@%s" % datetime.datetime.utcnow().isoformat()
        )
        pemfile.save()
        print(pemfile.value)
