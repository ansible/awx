from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import UserManager
from django.core.exceptions import ImproperlyConfigured
from django.db import models
try:
    from django.utils.module_loading import import_module
except ImportError:
    """Handle older versions of Django"""
    from django.utils.importlib import import_module
from django.utils.translation import ugettext_lazy as _


__all__ = (
    'get_user_document',
)


MONGOENGINE_USER_DOCUMENT = getattr(
    settings, 'MONGOENGINE_USER_DOCUMENT', 'mongoengine.django.auth.User')


def get_user_document():
    """Get the user document class used for authentication.

    This is the class defined in settings.MONGOENGINE_USER_DOCUMENT, which
    defaults to `mongoengine.django.auth.User`.

    """

    name = MONGOENGINE_USER_DOCUMENT
    dot = name.rindex('.')
    module = import_module(name[:dot])
    return getattr(module, name[dot + 1:])


class MongoUserManager(UserManager):
    """A User manager wich allows the use of MongoEngine documents in Django.

    To use the manager, you must tell django.contrib.auth to use MongoUser as
    the user model. In you settings.py, you need:

        INSTALLED_APPS = (
            ...
            'django.contrib.auth',
            'mongoengine.django.mongo_auth',
            ...
        )
        AUTH_USER_MODEL = 'mongo_auth.MongoUser'

    Django will use the model object to access the custom Manager, which will
    replace the original queryset with MongoEngine querysets.

    By default, mongoengine.django.auth.User will be used to store users. You
    can specify another document class in MONGOENGINE_USER_DOCUMENT in your
    settings.py.

    The User Document class has the same requirements as a standard custom user
    model: https://docs.djangoproject.com/en/dev/topics/auth/customizing/

    In particular, the User Document class must define USERNAME_FIELD and
    REQUIRED_FIELDS.

    `AUTH_USER_MODEL` has been added in Django 1.5.

    """

    def contribute_to_class(self, model, name):
        super(MongoUserManager, self).contribute_to_class(model, name)
        self.dj_model = self.model
        self.model = get_user_document()

        self.dj_model.USERNAME_FIELD = self.model.USERNAME_FIELD
        username = models.CharField(_('username'), max_length=30, unique=True)
        username.contribute_to_class(self.dj_model, self.dj_model.USERNAME_FIELD)

        self.dj_model.REQUIRED_FIELDS = self.model.REQUIRED_FIELDS
        for name in self.dj_model.REQUIRED_FIELDS:
            field = models.CharField(_(name), max_length=30)
            field.contribute_to_class(self.dj_model, name)


    def get(self, *args, **kwargs):
        try:
            return self.get_query_set().get(*args, **kwargs)
        except self.model.DoesNotExist:
            # ModelBackend expects this exception
            raise self.dj_model.DoesNotExist

    @property
    def db(self):
        raise NotImplementedError

    def get_empty_query_set(self):
        return self.model.objects.none()

    def get_query_set(self):
        return self.model.objects


class MongoUser(models.Model):
    """"Dummy user model for Django.

    MongoUser is used to replace Django's UserManager with MongoUserManager.
    The actual user document class is mongoengine.django.auth.User or any
    other document class specified in MONGOENGINE_USER_DOCUMENT.

    To get the user document class, use `get_user_document()`.

    """

    objects = MongoUserManager()

    class Meta:
        app_label = 'mongo_auth'

    def set_password(self, password):
        """Doesn't do anything, but works around the issue with Django 1.6."""
        make_password(password)
