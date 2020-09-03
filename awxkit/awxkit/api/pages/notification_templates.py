from awxkit.api.mixins import HasCreate, HasCopy, DSAdapter
from awxkit.api.pages import Organization
from awxkit.api.resources import resources
from awxkit.config import config
import awxkit.exceptions as exc
from awxkit.utils import not_provided, random_title, suppress, PseudoNamespace
from . import base
from . import page


job_results = ('any', 'error', 'success')
notification_types = (
    'email',
    'irc',
    'pagerduty',
    'slack',
    'twilio',
    'webhook',
    'mattermost',
    'grafana',
    'rocketchat')


class NotificationTemplate(HasCopy, HasCreate, base.Base):

    dependencies = [Organization]
    NATURAL_KEY = ('organization', 'name')

    def test(self):
        """Create test notification"""
        assert 'test' in self.related, \
            "No such related attribute 'test'"

        # trigger test notification
        notification_id = self.related.test.post().notification

        # return notification page
        notifications_pg = self.get_related(
            'notifications', id=notification_id).wait_until_count(1)
        assert notifications_pg.count == 1, \
            "test notification triggered (id:%s) but notification not found in response at %s/notifications/" % \
            (notification_id, self.url)
        return notifications_pg.results[0]

    def silent_delete(self):
        """Delete the Notification Template, ignoring the exception that is raised
        if there are notifications pending.
        """
        try:
            super(NotificationTemplate, self).silent_delete()
        except (exc.MethodNotAllowed):
            pass

    def payload(self, organization, notification_type='slack', messages=not_provided, **kwargs):
        payload = PseudoNamespace(
            name=kwargs.get('name') or 'NotificationTemplate ({0}) - {1}' .format(
                notification_type,
                random_title()),
            description=kwargs.get('description') or random_title(10),
            organization=organization.id,
            notification_type=notification_type)
        if messages != not_provided:
            payload['messages'] = messages

        notification_configuration = kwargs.get(
            'notification_configuration', {})
        payload.notification_configuration = notification_configuration

        if payload.notification_configuration == {}:
            services = config.credentials.notification_services

            if notification_type == 'email':
                fields = (
                    'host',
                    'username',
                    'password',
                    'port',
                    'use_ssl',
                    'use_tls',
                    'sender',
                    'recipients')
                cred = services.email
            elif notification_type == 'irc':
                fields = (
                    'server',
                    'port',
                    'use_ssl',
                    'password',
                    'nickname',
                    'targets')
                cred = services.irc
            elif notification_type == 'pagerduty':
                fields = ('client_name', 'service_key', 'subdomain', 'token')
                cred = services.pagerduty
            elif notification_type == 'slack':
                fields = ('channels', 'token')
                cred = services.slack
            elif notification_type == 'twilio':
                fields = (
                    'account_sid',
                    'account_token',
                    'from_number',
                    'to_numbers')
                cred = services.twilio
            elif notification_type == 'webhook':
                fields = ('url', 'headers')
                cred = services.webhook
            elif notification_type == 'mattermost':
                fields = (
                    'mattermost_url',
                    'mattermost_username',
                    'mattermost_channel',
                    'mattermost_icon_url',
                    'mattermost_no_verify_ssl')
                cred = services.mattermost
            elif notification_type == 'grafana':
                fields = ('grafana_url',
                          'grafana_key')
                cred = services.grafana
            elif notification_type == 'rocketchat':
                fields = ('rocketchat_url',
                          'rocketchat_no_verify_ssl')
                cred = services.rocketchat
            else:
                raise ValueError(
                    'Unknown notification_type {0}'.format(notification_type))

            for field in fields:
                if field == 'bot_token':
                    payload_field = 'token'
                else:
                    payload_field = field
                value = kwargs.get(field, cred.get(field, not_provided))
                if value != not_provided:
                    payload.notification_configuration[payload_field] = value

        return payload

    def create_payload(
            self,
            name='',
            description='',
            notification_type='slack',
            organization=Organization,
            messages=not_provided,
            **kwargs):
        if notification_type not in notification_types:
            raise ValueError(
                'Unsupported notification type "{0}".  Please use one of {1}.' .format(
                    notification_type, notification_types))
        self.create_and_update_dependencies(organization)
        payload = self.payload(
            organization=self.ds.organization,
            notification_type=notification_type,
            name=name,
            description=description,
            messages=messages,
            **kwargs)
        payload.ds = DSAdapter(self.__class__.__name__, self._dependency_store)
        return payload

    def create(
            self,
            name='',
            description='',
            notification_type='slack',
            organization=Organization,
            messages=not_provided,
            **kwargs):
        payload = self.create_payload(
            name=name,
            description=description,
            notification_type=notification_type,
            organization=organization,
            messages=messages,
            **kwargs)
        return self.update_identity(
            NotificationTemplates(
                self.connection).post(payload))

    def associate(self, resource, job_result='any'):
        """Associates a NotificationTemplate with the provided resource"""
        return self._associate(resource, job_result)

    def disassociate(self, resource, job_result='any'):
        """Disassociates a NotificationTemplate with the provided resource"""
        return self._associate(resource, job_result, disassociate=True)

    def _associate(self, resource, job_result='any', disassociate=False):
        if job_result not in job_results:
            raise ValueError(
                'Unsupported job_result type "{0}".  Please use one of {1}.' .format(
                    job_result, job_results))

        result_attr = 'notification_templates_{0}'.format(job_result)
        if result_attr not in resource.related:
            raise ValueError(
                'Unsupported resource "{0}".  Does not have a related {1} field.' .format(
                    resource, result_attr))

        payload = dict(id=self.id)
        if disassociate:
            payload['disassociate'] = True

        with suppress(exc.NoContent):
            getattr(resource.related, result_attr).post(payload)


page.register_page([resources.notification_template,
                    (resources.notification_templates, 'post'),
                    (resources.notification_template_copy, 'post'),
                    resources.notification_template_any,
                    resources.notification_template_started,
                    resources.notification_template_error,
                    resources.notification_template_success,
                    resources.notification_template_approval], NotificationTemplate)


class NotificationTemplates(page.PageList, NotificationTemplate):

    pass


page.register_page([resources.notification_templates,
                    resources.related_notification_templates,
                    resources.notification_templates_any,
                    resources.notification_templates_started,
                    resources.notification_templates_error,
                    resources.notification_templates_success,
                    resources.notification_templates_approvals],
                   NotificationTemplates)


class NotificationTemplateCopy(base.Base):

    pass


page.register_page(resources.notification_template_copy, NotificationTemplateCopy)


class NotificationTemplateTest(base.Base):

    pass


page.register_page(
    resources.notification_template_test,
    NotificationTemplateTest)
