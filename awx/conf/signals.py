# Python
import logging

# Django
from django.conf import settings
from django.core.cache import cache
from django.core.signals import setting_changed
from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver

# AWX
from awx.conf import settings_registry
from awx.conf.models import Setting

logger = logging.getLogger('awx.conf.signals')

__all__ = []


def handle_setting_change(key, for_delete=False):
    # When a setting changes or is deleted, remove its value from cache along
    # with any other settings that depend on it.
    setting_keys = [key]
    for dependent_key in settings_registry.get_dependent_settings(key):
        # Note: Doesn't handle multiple levels of dependencies!
        setting_keys.append(dependent_key)
    # NOTE: This block is probably duplicated.
    cache_keys = {Setting.get_cache_key(k) for k in setting_keys}
    cache.delete_many(cache_keys)

    # if we have changed a setting, we want to avoid mucking with the in-memory cache entirely
    settings._awx_conf_memoizedcache.clear()

    # Send setting_changed signal with new value for each setting.
    for setting_key in setting_keys:
        setting_changed.send(sender=Setting, setting=setting_key, value=getattr(settings, setting_key, None), enter=not bool(for_delete))


@receiver(post_save, sender=Setting)
def on_post_save_setting(sender, **kwargs):
    instance = kwargs['instance']
    # Skip for user-specific settings.
    if instance.user:
        return
    handle_setting_change(instance.key)


@receiver(pre_delete, sender=Setting)
def on_pre_delete_setting(sender, **kwargs):
    instance = kwargs['instance']
    # Skip for user-specific settings.
    if instance.user:
        return
    # Save instance key (setting name) for post_delete.
    instance._saved_key_ = instance.key


@receiver(post_delete, sender=Setting)
def on_post_delete_setting(sender, **kwargs):
    instance = kwargs['instance']
    key = getattr(instance, '_saved_key_', None)
    if key:
        handle_setting_change(key, True)


@receiver(setting_changed)
def disable_local_auth(**kwargs):
    if (kwargs['setting'], kwargs['value']) == ('DISABLE_LOCAL_AUTH', True):
        from django.contrib.auth.models import User
        from oauth2_provider.models import RefreshToken
        from awx.main.models.oauth import OAuth2AccessToken
        from awx.main.management.commands.revoke_oauth2_tokens import revoke_tokens

        logger.warning("Triggering token invalidation for local users.")

        qs = User.objects.filter(profile__ldap_dn='', enterprise_auth__isnull=True, social_auth__isnull=True)
        revoke_tokens(RefreshToken.objects.filter(revoked=None, user__in=qs))
        revoke_tokens(OAuth2AccessToken.objects.filter(user__in=qs))
