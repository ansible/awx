import logging

from django.contrib.auth.backends import ModelBackend

from awx.conf import db_settings

logger = logging.getLogger('awx.main.backends')


class AWXModelBackend(ModelBackend):
    def authenticate(self, request, **kwargs):
        if db_settings.DISABLE_LOCAL_AUTH:
            logger.warning(f"User '{kwargs['username']}' attempted login through the disabled local authentication system.")
            return
        return super().authenticate(request, **kwargs)
