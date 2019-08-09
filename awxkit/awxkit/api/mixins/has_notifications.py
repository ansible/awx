from awxkit.utils import suppress
import awxkit.exceptions as exc


notification_endpoints = ("notification_templates", "notification_templates_started", "notification_templates_error",
                          "notification_templates_success")


class HasNotifications(object):

    def add_notification_template(self, notification_template, endpoint="notification_templates_success"):
        if endpoint not in notification_endpoints:
            raise ValueError('Unsupported notification endpoint "{0}". Please use one of {1}.'
                             .format(endpoint, notification_endpoints))
        with suppress(exc.NoContent):
            self.related[endpoint].post(dict(id=notification_template.id))

    def remove_notification_template(self, notification_template, endpoint="notification_templates_success"):
        if endpoint not in notification_endpoints:
            raise ValueError('Unsupported notification endpoint "{0}". Please use one of {1}.'
                             .format(endpoint, notification_endpoints))
        with suppress(exc.NoContent):
            self.related[endpoint].post(dict(id=notification_template.id, disassociate=notification_template.id))
