import re
from typing import Any

from django.conf import settings
from awx.conf import settings_registry
from ansible_base.authentication.models import Authenticator, AuthenticatorMap

import logging

logger = logging.getLogger('awx.conf.migrations')


DAB_LDAP_AUTHENTICATOR_KEYS = {
    "SERVER_URI": True,
    "BIND_DN": False,
    "BIND_PASSWORD": False,
    "CONNECTION_OPTIONS": False,
    "GROUP_TYPE": True,
    "GROUP_TYPE_PARAMS": True,
    "GROUP_SEARCH": False,
    "START_TLS": False,
    "USER_DN_TEMPLATE": True,
    "USER_ATTR_MAP": True,
    "USER_SEARCH": False,
}


def get_awx_ldap_settings() -> dict[str, dict[str, Any]]:
    awx_ldap_settings = {}

    for awx_ldap_setting in settings_registry.get_registered_settings(category_slug='ldap'):
        key = awx_ldap_setting.removeprefix("AUTH_LDAP_")
        value = getattr(settings, awx_ldap_setting, None)
        awx_ldap_settings[key] = value

    grouped_settings = {}

    for key, value in awx_ldap_settings.items():
        match = re.search(r'(\d+)', key)
        index = int(match.group()) if match else 0
        new_key = re.sub(r'\d+_', '', key)

        if index not in grouped_settings:
            grouped_settings[index] = {}

        grouped_settings[index][new_key] = value
        if new_key == "GROUP_TYPE" and value:
            grouped_settings[index][new_key] = type(value).__name__

        if new_key == "SERVER_URI" and value:
            value = value.split(", ")

    return grouped_settings


def is_enabled(settings, keys):
    for key, required in keys.items():
        if required and not settings.get(key):
            return False
    return True


def format_config_data(enabled, awx_settings, type, keys, name):
    config = {
        "type": f"awx.authentication.authenticator_plugins.{type}",
        "name": name,
        "enabled": enabled,
        "create_objects": True,
        "users_unique": False,
        "remove_users": True,
        "configuration": {},
    }
    for k in keys:
        v = awx_settings.get(k)
        config["configuration"].update({k: v})

    return config


def create_auth_maps(awx_settings, authenticator_id):
    map_configs = []
    map_config = {}
    if "USER_FLAGS_BY_GROUP" in awx_settings:
        for flag in awx_settings.get("USER_FLAGS_BY_GROUP"):
            groups = awx_settings.get("USER_FLAGS_BY_GROUP")[flag]
            if type(groups) is str:
                groups = [groups]

            map_config = {
                "authenticator": authenticator_id,
                "revoke": True,
                "map_type": flag,
                "team": None,
                "organization": None,
                "triggers": {
                    "groups": {
                        "has_or": groups,
                    }
                },
            }
            map_configs.append(map_config)

        if "ORGANIZATION_MAP" in awx_settings:
            for organization_name in awx_settings.get("ORGANIZATION_MAP").keys():
                organization = awx_settings.get("ORGANIZATION_MAP")[organization_name]
                for user_type in ['admins', 'users']:
                    if user_type in organization:
                        if organization[user_type] is None:
                            continue
                        if organization[user_type] is False:
                            triggers = {"never": {}}
                        elif organization[user_type] is True:
                            triggers = {"always": {}}
                        else:
                            if type(organization[user_type]) is str:
                                organization[user_type] = [organization[user_type]]

                            triggers = {"groups": {"has_or": organization[user_type]}}

                        map_config = {
                            "authenticator": authenticator_id,
                            "revoke": organization.get(f'remove_{user_type}', False),
                            "map_type": "team",
                            "team": f"Organization {user_type.title()}",
                            "organization": organization_name,
                            "triggers": triggers,
                        }
                        map_configs.append(map_config)

        if "TEAM_MAP" in awx_settings:
            for team_name in awx_settings.get("TEAM_MAP").keys():
                team = awx_settings.get("TEAM_MAP")[team_name]
                if team['users'] is None:
                    continue
                if team['users'] is False:
                    triggers = {"never": {}}
                elif team['users'] is True:
                    triggers = {"always": {}}
                else:
                    if type(team['users']) is str:
                        team['users'] = [team['users']]

                    triggers = {"groups": {"has_or": team['users']}}

                map_config = {
                    "authenticator": authenticator_id,
                    "revoke": team.get('remove', False),
                    "map_type": "team",
                    "team": team_name,
                    "organization": team.get('organization', 'You have a team with no organization'),
                    "triggers": triggers,
                }
                map_configs.append(map_config)

        require_group = awx_settings.get("REQUIRE_GROUP", None)
        if require_group:
            map_config = {
                "authenticator": authenticator_id,
                "revoke": False,
                "map_type": "allow",
                "team": None,
                "organization": None,
                "triggers": {"groups": {"has_and": [require_group]}},
            }
            map_configs.append(map_config)

        deny_group = awx_settings.get("DENY_GROUP", None)
        if deny_group:
            map_config = {
                "authenticator": authenticator_id,
                "revoke": False,
                "map_type": "allow",
                "team": None,
                "organization": None,
                "triggers": {"groups": {"has_not": [require_group]}},
            }
            map_configs.append(map_config)

    return map_configs


def create_ldap_auth_and_authmap(apps, schema_editor):
    logger.info('Creating django-ansible-base LDAP authenticators and authenticator maps...')
    awx_ldap_group_settings = get_awx_ldap_settings()
    for awx_ldap_name, awx_ldap_settings in enumerate(awx_ldap_group_settings.values()):
        enabled = is_enabled(awx_ldap_settings, DAB_LDAP_AUTHENTICATOR_KEYS)
        if enabled:
            ldap_config = format_config_data(
                enabled,
                awx_ldap_settings,
                "ldap",
                DAB_LDAP_AUTHENTICATOR_KEYS,
                str(awx_ldap_name),
            )
            try:
                authenticator = Authenticator.objects.create(**ldap_config)
                authenticator.save()
            except Exception as ex:
                logger.error(f"Failed to create Authenticator from LDAP config {awx_ldap_name} with error {ex}.")

            ldap_auth_maps = create_auth_maps(awx_ldap_settings, authenticator.id)
            for ldap_map in ldap_auth_maps:
                auth_map = AuthenticatorMap.objects.create(**ldap_map)
                auth_map.save()
