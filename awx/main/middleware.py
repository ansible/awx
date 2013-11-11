from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import pre_save
from django.utils.functional import curry
from awx.main.models.activity_stream import ActivityStream
import json
import urllib2

class ActivityStreamMiddleware(object):

    def process_request(self, request):
        self.isActivityStreamEvent = False
        if hasattr(request, 'user') and hasattr(request.user, 'is_authenticated') and request.user.is_authenticated():
            user = request.user
        else:
            user = None

        set_actor = curry(self.set_actor, user)
        pre_save.connect(set_actor, sender=ActivityStream, dispatch_uid=(self.__class__, request), weak=False)

    def process_response(self, request, response):
        pre_save.disconnect(dispatch_uid=(self.__class__, request))
        if self.isActivityStreamEvent:
            if "current_user" in request.COOKIES and "id" in request.COOKIES["current_user"]:
                userInfo = json.loads(urllib2.unquote(request.COOKIES['current_user']).decode('utf8'))
                userActual = User.objects.get(id=int(userInfo['id']))
                self.instance.user = userActual
                self.instance.save()
        return response

    def set_actor(self, user, sender, instance, **kwargs):
        if sender == ActivityStream:
            if isinstance(user, User) and instance.user is None:
                instance.user = user
            else:
                self.isActivityStreamEvent = True
                self.instance = instance
        else:
                self.isActivityStreamEvent = False
