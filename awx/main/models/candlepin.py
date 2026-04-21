# Copyright (c) 2026 Ansible, Inc.
# All Rights Reserved.

from django.db import models
from django.utils.translation import gettext_lazy as _
from solo.models import SingletonModel
from awx.main.models.base import PasswordFieldsModel

__all__ = ['CandlepinCertificate']

# Placeholder UUID used before a real consumer is registered
# This constant is also defined in awx.main.utils.licensing for use outside the model
CANDLEPIN_UUID_PLACEHOLDER = '00000000-0000-0000-0000-000000000000'


class CandlepinCertificate(SingletonModel, PasswordFieldsModel):
    """
    Model to store Candlepin consumer identity certificate for analytics authentication.

    This model stores the certificate and private key obtained from Candlepin during
    consumer registration. The certificate is used for mTLS authentication when
    uploading analytics data. Both cert_pem and key_pem are encrypted at rest.

    Only one instance should exist (singleton pattern) - the certificate for this AWX
    instance's Candlepin consumer. This is enforced by inheriting from SingletonModel.
    """

    PASSWORD_FIELDS = ('cert_pem', 'key_pem')

    class Meta:
        app_label = 'main'
        verbose_name = _('Candlepin Certificate')
        verbose_name_plural = _('Candlepin Certificates')
        db_table = 'main_candlepin_certificate'

    consumer_uuid = models.CharField(
        max_length=255,
        blank=True,
        default=CANDLEPIN_UUID_PLACEHOLDER,
        help_text=_('Candlepin consumer UUID'),
    )

    cert_pem = models.TextField(
        blank=True,
        default='',
        help_text=_('PEM-encoded certificate (encrypted)'),
    )

    key_pem = models.TextField(
        blank=True,
        default='',
        help_text=_('PEM-encoded private key (encrypted)'),
    )

    serial_number = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text=_('Certificate serial number for tracking'),
    )

    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Certificate expiry timestamp'),
    )

    def __str__(self):
        return f'Candlepin Certificate (UUID: {self.consumer_uuid})'

    @classmethod
    def get_instance(cls):
        """
        Get the singleton instance of the Candlepin certificate.
        Returns the singleton instance (creates it with placeholder values if it doesn't exist).

        This is a compatibility wrapper around SingletonModel's get_solo() method.
        """
        return cls.get_solo()

    @classmethod
    def get_or_create_instance(cls):
        """
        Get or create the singleton instance.

        This is a compatibility wrapper around SingletonModel's get_solo() method.
        """
        return cls.get_solo()

    def update_certificate(self, cert_pem, key_pem, consumer_uuid=None, serial_number=None, expires_at=None):
        """
        Update the certificate data.

        Args:
            cert_pem: PEM-encoded certificate string
            key_pem: PEM-encoded private key string
            consumer_uuid: Optional new consumer UUID
            serial_number: Optional certificate serial number
            expires_at: Optional certificate expiry timestamp
        """
        self.cert_pem = cert_pem
        self.key_pem = key_pem
        if consumer_uuid is not None:
            self.consumer_uuid = consumer_uuid
        if serial_number is not None:
            self.serial_number = serial_number
        if expires_at is not None:
            self.expires_at = expires_at
        self.save()

    def has_valid_data(self):
        """
        Check if the instance has valid certificate data (not placeholder).
        """
        return self.consumer_uuid and self.consumer_uuid != CANDLEPIN_UUID_PLACEHOLDER and self.cert_pem and self.key_pem
