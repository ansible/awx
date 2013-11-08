from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import pre_save
from django.utils.functional import curry
from awx.main.models.activity_stream import ActivityStream


class ActivityStreamMiddleware(object):

    def process_request(self, request):
        if hasattr(request, 'user') and hasattr(request.user, 'is_authenticated') and request.user.is_authenticated():
            user = request.user
        else:
            user = None

        set_actor = curry(self.set_actor, user)
        pre_save.connect(set_actor, sender=ActivityStream, dispatch_uid=(self.__class__, request), weak=False)

    def process_response(self, request, response):
        pre_save.disconnect(dispatch_uid=(self.__class__, request))
        return response

    def set_actor(self, user, sender, instance, **kwargs):
        if sender == ActivityStream and isinstance(user, User) and instance.user is None:
            instance.user = user
