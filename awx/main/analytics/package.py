import base64
import json
from insights_analytics_collector import Package as AnalyticsPackage

from awx.main.utils import get_awx_http_client_headers, set_environ

from django.conf import settings


class Package(AnalyticsPackage):
    CERT_PATH = "/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem"
    PAYLOAD_CONTENT_TYPE = "application/vnd.redhat.tower.tower_payload+tgz"

    def _tarname_base(self):
        timestamp = self.collector.gather_until
        return f'{settings.SYSTEM_UUID}-{timestamp.strftime("%Y-%m-%d-%H%M%S%z")}'

    def get_ingress_url(self):
        return getattr(settings, 'AUTOMATION_ANALYTICS_URL', None)

    def _get_rh_user(self):
        return getattr(settings, 'REDHAT_USERNAME', None)

    def _get_rh_password(self):
        return getattr(settings, 'REDHAT_PASSWORD', None)

    def _get_x_rh_identity(self):
        identity = {"identity": {"type": "User", "account_number": "0000001", "user": {"is_org_admin": True},
                                 "internal": {"org_id": "000001"}}}
        identity = base64.b64encode(json.dumps(identity).encode('utf8'))
        return identity

    def _get_http_request_headers(self):
        return get_awx_http_client_headers()

    def shipping_auth_mode(self):
        return self.SHIPPING_AUTH_IDENTITY

    def _send_data(self, url, files, session):
        with set_environ(**settings.AWX_TASK_ENV):
            if self.shipping_auth_mode() == self.SHIPPING_AUTH_USERPASS:
                response = session.post(
                    url, files=files, verify=self.CERT_PATH,
                    auth=(self._get_rh_user(), self._get_rh_password()), headers=session.headers, timeout=(31, 31)
                )
            else:
                response = session.post(
                    url, files=files, headers=session.headers, timeout=(31, 31)
                )

        # Accept 2XX status_codes
        if response.status_code >= 300:
            self.logger.error('Upload failed with status {}, {}'.format(response.status_code, response.text))
            return False

        return True
