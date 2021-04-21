from contextlib import suppress

import awxkit.exceptions as exc


notification_endpoints = ("notification_templates", "notification_templates_started", "notification_templates_error", "notification_templates_success")
wfjt_notification_endpoints = notification_endpoints + ('notification_templates_approvals',)


class HasNotifications(object):
    def add_notification_template(self, notification_template, endpoint="notification_templates_success"):
        from awxkit.api.pages.workflow_job_templates import WorkflowJobTemplate

        supported_endpoints = wfjt_notification_endpoints if isinstance(self, WorkflowJobTemplate) else notification_endpoints
        if endpoint not in supported_endpoints:
            raise ValueError('Unsupported notification endpoint "{0}". Please use one of {1}.'.format(endpoint, notification_endpoints))
        with suppress(exc.NoContent):
            self.related[endpoint].post(dict(id=notification_template.id))

    def remove_notification_template(self, notification_template, endpoint="notification_templates_success"):
        from awxkit.api.pages.workflow_job_templates import WorkflowJobTemplate

        supported_endpoints = wfjt_notification_endpoints if isinstance(self, WorkflowJobTemplate) else notification_endpoints
        if endpoint not in supported_endpoints:
            raise ValueError('Unsupported notification endpoint "{0}". Please use one of {1}.'.format(endpoint, notification_endpoints))
        with suppress(exc.NoContent):
            self.related[endpoint].post(dict(id=notification_template.id, disassociate=notification_template.id))
