import re
from typing import Any

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

name_counter = 1


def get_awx_ldap_settings(apps) -> dict[str, dict[str, Any]]:
    awx_ldap_settings = {}
    Setting = apps.get_model('conf', 'Setting')
    qs = Setting.objects.filter(key__startswith="AUTH_LDAP_")

    for awx_ldap_setting in qs:
        key = awx_ldap_setting.key.removeprefix("AUTH_LDAP_")
        value = awx_ldap_setting.value
        awx_ldap_settings[key] = value

    grouped_settings = {}

    for key, value in awx_ldap_settings.items():
        match = re.search(r'(\d+)', key)
        index = int(match.group()) if match else 0
        new_key = re.sub(r'\d+_', '', key)

        if index not in grouped_settings:
            grouped_settings[index] = {}

        grouped_settings[index][new_key] = value

        if new_key == "BIND_PASSWORD":
            # password is encrypted in the db. user will have to set it again
            grouped_settings[index][new_key] = "password"

        if new_key == "GROUP_TYPE" and value:
            grouped_settings[index][new_key] = value

        if new_key == "SERVER_URI" and value:
            value = value.split(", ")
            grouped_settings[index][new_key] = value

    return grouped_settings


def is_enabled(settings, keys):
    for key, required in keys.items():
        if required and not settings.get(key):
            return False
    return True


def format_config_data(enabled, awx_settings, auth_type, keys, name):
    config = {
        "type": f"ansible_base.authentication.authenticator_plugins.{auth_type}",
        "name": name,
        "enabled": enabled,
        "create_objects": True,
        "users_unique": False,
        "remove_users": True,
        "configuration": {},
        "slug": name.lower(),
        "category": auth_type,
    }
    for k in keys:
        v = awx_settings.get(k)
        config["configuration"].update({k: v})

    return config


def create_auth_maps(awx_settings, authenticator):
    map_configs = []
    map_config = {}
    if "USER_FLAGS_BY_GROUP" in awx_settings:
        for flag in awx_settings.get("USER_FLAGS_BY_GROUP"):
            groups = awx_settings.get("USER_FLAGS_BY_GROUP")[flag]
            if type(groups) is str:
                groups = [groups]

            map_config = {
                "authenticator": authenticator,
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
                            "authenticator": authenticator,
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
                    "authenticator": authenticator,
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
                "authenticator": authenticator,
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
                "authenticator": authenticator,
                "revoke": False,
                "map_type": "allow",
                "team": None,
                "organization": None,
                "triggers": {"groups": {"has_not": [require_group]}},
            }
            map_configs.append(map_config)

    return map_configs


def create_ldap_auth_and_authmap(apps, schema_editor):
    global name_counter
    logger.info('Creating django-ansible-base LDAP authenticators and authenticator maps...')
    awx_ldap_group_settings = get_awx_ldap_settings(apps)
    for awx_ldap_name, awx_ldap_settings in awx_ldap_group_settings.items():
        enabled = is_enabled(awx_ldap_settings, DAB_LDAP_AUTHENTICATOR_KEYS)
        if enabled:
            ldap_config = format_config_data(
                enabled,
                awx_ldap_settings,
                "ldap",
                DAB_LDAP_AUTHENTICATOR_KEYS,
                f"LDAP_{awx_ldap_name}",
            )
            try:
                Authenticator = apps.get_model('dab_authentication', 'Authenticator')
                AuthenticatorMap = apps.get_model('dab_authentication', 'AuthenticatorMap')
                authenticator = Authenticator.objects.create(**ldap_config)
                authenticator.save()

                ldap_auth_maps = create_auth_maps(awx_ldap_settings, authenticator)
                for ldap_map in ldap_auth_maps:
                    # AuthenticatorMaps need a unique name
                    ldap_map["name"] = f"Rule #{name_counter}"
                    name_counter += 1
                    auth_map = AuthenticatorMap.objects.create(**ldap_map)
                    auth_map.save()
            except Exception as ex:
                logger.error(f"Failed to create Authenticator from LDAP config {awx_ldap_name} with error {ex}.")
