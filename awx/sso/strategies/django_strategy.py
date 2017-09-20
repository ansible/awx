# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from social.strategies.django_strategy import DjangoStrategy


class AWXDjangoStrategy(DjangoStrategy):
    """A DjangoStrategy for python-social-auth containing
       fixes and updates from social-app-django

       TODO: Revert back to using the default DjangoStrategy after
       we upgrade to social-core / social-app-django. We will also
       want to ensure we update the SOCIAL_AUTH_STRATEGY setting.
    """

    def request_port(self):
        """Port in use for this request
           https://github.com/python-social-auth/social-app-django/blob/master/social_django/strategy.py#L76
        """
        try:  # django >= 1.9
            return self.request.get_port()
        except AttributeError:  # django < 1.9
            host_parts = self.request.get_host().split(':')
            try:
                return host_parts[1]
            except IndexError:
                return self.request.META['SERVER_PORT']
