'''
Handles Authentication with RHSM and retrieval of the entitlement cert.

Purpose:
 - Open connection with RHSM API and handle authentication
 - Retrieve accessible subscriptions
 - Download the entitlement certificate
'''

import logging
import inspect

from awx.main.utils.licensing import Licenser

from django.conf import settings
from rhsm.connection import UEPConnection, RestlibException


logger = logging.getLogger('awx.main.utils.subscriptions')


def trace():
    frame = inspect.currentframe()
    frame = frame.f_back

    (filename, line_number, function_name, lines, index) = inspect.getframeinfo(frame)
    return f"{filename}:{function_name}():{line_number}"


class SubscriptionManagerSettingsError(Exception):
    def __init__(self, error_msgs):
        self.error_msgs = error_msgs
        super().__init__(error_msgs)


class SubscriptionManagerRefreshError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)


class SubscriptionManager:
    def __init__(self, redhat_username: str, redhat_password: str, consumer_id: str, verify: bool):
        self.rhsm = UEPConnection(username=redhat_username, password=redhat_password, insecure=not verify)
        self.consumer_id = consumer_id

    @staticmethod
    def get_init_params():
        consumer = getattr(settings, 'ENTITLEMENT_CONSUMER', dict())
        consumer_uuid = consumer.get('uuid', None)
        username = getattr(settings, 'SUBSCRIPTIONS_USERNAME', None)
        password = getattr(settings, 'SUBSCRIPTIONS_PASSWORD', None)
        verify = getattr(settings, 'REDHAT_CANDLEPIN_VERIFY', True)

        errors = []
        if not consumer:
            errors.append("Setting ENTITLEMENT_CONSUMER is empty. This can happen if you manually uploaded an entitlement or have not yet registered Tower.")
        if not consumer_uuid:
            errors.append("Setting ENTITLEMENT_CONSUMER['uuid'] not found and is needed to refresh the certificate from RHSM or Satellite.")
        if not username:
            errors.append("Setting SUBSCRIPTIONS_USERNAME is empty and is needed to refresh the certificate from RHSM or Satellite.")
        if not password:
            errors.append("Setting SUBSCRIPTIONS_PASSWORD is empty and is needed to refresh the certificate from RHSM or Satellite.")

        if errors:
            raise SubscriptionManagerSettingsError(errors)

        return (username, password, consumer_uuid, verify)

    def get_entitlement_id(self):
        '''
        This function relies on there being 1 and only 1 entitlement associated with the consumer.
        If there are more, this function returns None.

        Returns:
            (string): The unique identifer for the singular entitlement associated with the consumer.
        '''

        try:
            res = self.rhsm.getEntitlementList(self.consumer_id)
        except RestlibException as e:
            raise SubscriptionManagerRefreshError(f"{trace()} RHSM error {e}")

        if len(res) == 0:
            raise SubscriptionManagerRefreshError(f"No entitlements for consumer '{self.consumer_id}' found.")
        if len(res) > 1:
            raise SubscriptionManagerRefreshError(f"Found '{len(res)}' entitlements for consumer '{self.consumer_id}' when 1 was expected.")
        if 'id' not in res[0]:
            raise SubscriptionManagerRefreshError("Key 'id' not found in entitlement")
        return res[0]['id']

    def get_certificate_for_entitlement(self, entitlement_id: str):
        '''
        Returns the first certificate found in an entitlement.
        If a certificate is not found an empty dict is returned

        Returns:
            (dict): certificate dict from remote server.

        '''
        try:
            res = self.rhsm.getEntitlement(entitlement_id)
        except RestlibException as e:
            raise SubscriptionManagerRefreshError(f"{trace()} RHSM error {e}")

        return res.get('certificates', [{}])[0]

    def refresh_entitlement_certs(self):
        '''
        If this function returns without raising an error then the certificat was refreshed.
        Returning old and new certificates are best effort.

        Returns:
            (string, string): new certificate, old certificate.
            old cert or new cert returned may be ''
        '''
        regen_ret = False
        old_certificate = ''
        new_certificate = ''

        entitlement_id = self.get_entitlement_id()
        try:
            old_certificate = self.get_certificate_for_entitlement(entitlement_id)
        except SubscriptionManagerRefreshError as e:
            logger.warning(f"Failed to find existing entitlement '{entitlement_id}' for reasons of {e.message}.")

        regen_ret = self.rhsm.regenEntitlementCertificate(self.consumer_id, entitlement_id, lazy_regen=False) # Eats all HTTP exceptions
        if not regen_ret:
            raise SubscriptionManagerRefreshError(f"Failed to refresh entitlement '{entitlement_id}' for consumer '{self.consumer_id}' on the remote server.")
        logger.info(f"Successfully refreshed certificate for entitlement '{entitlement_id}' on the remote server.")

        try:
            new_certificate = self.get_certificate_for_entitlement(entitlement_id)
        except SubscriptionManagerRefreshError as e:
            logger.warning(f"Failed to retrieve the new certificate from the remote server for reasons of {e.message}.")

        return (new_certificate, old_certificate)

    def refresh_entitlement_certs_and_save(self):
        '''
        Refresh entitlement certs in RHSM and save the new certificate into Tower database.
        '''
        (new_cert, old_cert) = self.refresh_entitlement_certs()

        if not new_cert:
            raise SubscriptionManagerRefreshError("Did not save new entitlement certificate. Refresh succeeded but getting new cert failed.")

        settings.ENTITLEMENT_CERT = new_cert['cert'] + new_cert['key']
        logger.info(f"New certificate valid until {new_cert.get('serial', {}).get('expiration', 'NOT FOUND')}")
        logger.info("Successfully saved refreshed entitlement certificate to the database.")

        try:
            Licenser().validate(new_cert=True)
        except Exception(e):
            raise SubscriptionManagerRefreshError(f"Refreshed license and saved new license. However, validating new license failed '{e}'")
