from awxkit.api.mixins import HasStatus
from awxkit.api.resources import resources
from awxkit.utils import poll_until, seconds_since_date_string
from . import base
from . import page


class Notification(HasStatus, base.Base):
    def __str__(self):
        items = ['id', 'notification_type', 'status', 'error', 'notifications_sent', 'subject', 'recipients']
        info = []
        for item in [x for x in items if hasattr(self, x)]:
            info.append('{0}:{1}'.format(item, getattr(self, item)))
        output = '<{0.__class__.__name__} {1}>'.format(self, ', '.join(info))
        return output.replace('%', '%%')

    @property
    def is_successful(self):
        """Return whether the notification was created successfully. This means that:
        * self.status == 'successful'
        * self.error == False
        """
        return super(Notification, self).is_successful and not self.error

    def wait_until_status(self, status, interval=5, timeout=30, **kwargs):
        adjusted_timeout = timeout - seconds_since_date_string(self.created)
        return super(Notification, self).wait_until_status(status, interval, adjusted_timeout, **kwargs)

    def wait_until_completed(self, interval=5, timeout=240):
        """Notifications need a longer timeout, since the backend often has
        to wait for the request (sending the notification) to timeout itself
        """
        adjusted_timeout = timeout - seconds_since_date_string(self.created)
        return super(Notification, self).wait_until_completed(interval, adjusted_timeout)


page.register_page(resources.notification, Notification)


class Notifications(page.PageList, Notification):
    def wait_until_count(self, count, interval=10, timeout=60, **kw):
        """Poll notifications page until it is populated with `count` number of notifications."""
        poll_until(lambda: getattr(self.get(), 'count') == count, interval=interval, timeout=timeout, **kw)
        return self


page.register_page([resources.notifications, resources.related_notifications], Notifications)
