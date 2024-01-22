# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import logging
import typing as t

# Django
from django.conf import settings

from awx.main.models import Team
from awx.sso.common import create_org_and_teams, reconcile_users_org_team_mappings, get_orgs_by_ids
from awx.sso.social_pipeline import update_user_orgs, update_user_teams


logger = logging.getLogger('awx.sso.social_oidc_pipeline')


def populate_user(backend, details, user=None, *args, **kwargs):
    if not user:
        return

    # Build the in-memory settings for how this user should be modeled
    desired_org_state = {}
    desired_team_state = {}
    orgs_to_create = []
    teams_to_create = {}
    _update_user_orgs_by_scope(backend, desired_org_state, orgs_to_create, **kwargs)
    _update_user_teams_by_scope(desired_team_state, teams_to_create, **kwargs)
    update_user_orgs(backend, desired_org_state, orgs_to_create, user)
    update_user_teams(backend, desired_team_state, teams_to_create, user)

    # If the Azure AD Oauth2 adapter is allowed to create objects, lets do that first
    create_org_and_teams(orgs_to_create, teams_to_create, 'OIDC Generic', settings.SOCIAL_AUTH_OIDC_AUTO_CREATE_OBJECTS)

    # Finally reconcile the user
    reconcile_users_org_team_mappings(user, desired_org_state, desired_team_state, 'OIDC Generic')


def _update_user_orgs_by_scope(backend, desired_org_state, orgs_to_create, **kwargs):
    #
    # Map users into organizations based on SOCIAL_AUTH_OIDC_ORGANIZATION_REMOTE_MAP setting
    #
    org_map = settings.SOCIAL_AUTH_OIDC_ORGANIZATION_REMOTE_MAP

    user_types = ["member", "admin", "auditor"]

    # We need to load all of the orgs and remove the user from the role
    remove_values = {f'{user_type}_role': bool(org_map.get(f'remove_{user_type}s', True)) for user_type in user_types}
    all_orgs = get_orgs_by_ids()
    for role, remove_value in remove_values.items():
        if remove_value:
            for org_name in all_orgs.keys():
                if org_name not in desired_org_state:
                    desired_org_state[org_name] = {}
                desired_org_state[org_name][role] = not remove_value

    social_auth_scope_values = {
        f'social_auth_{user_type}_scope_values': kwargs.get('response', {}).get(org_map.get(f'social_auth_{user_type}_scope', "roles"), [])
        for user_type in user_types
    }

    for org in org_map.get('org_map', []):
        _org_name = org.get('organization', None)
        if _org_name is None:
            continue
        org_name = (backend.setting('ORGANIZATION_MAP') or {}).get(_org_name, {}).get('organization_alias', _org_name)

        if org_name not in orgs_to_create:
            orgs_to_create.append(org_name)

        default_social_auth_value = f'ORG_{org_name.upper().replace(" ", "_")}'
        if org_name not in desired_org_state:
            desired_org_state[org_name] = {}
        for user_type in user_types:
            if (
                org.get(f'social_auth_{user_type}_value', f"{default_social_auth_value}_{user_type.upper()}")
                in social_auth_scope_values[f'social_auth_{user_type}_scope_values']
            ):
                desired_org_state[org_name][f'{user_type}_role'] = True


def _update_user_teams_by_scope(desired_team_state, teams_to_create, **kwargs):
    #
    # Map users into teams based on SOCIAL_AUTH_OIDC_TEAM_REMOTE_MAP setting
    #
    team_map = settings.SOCIAL_AUTH_OIDC_TEAM_REMOTE_MAP
    social_auth_scope = team_map.get('social_auth_member_scope', "roles")

    user_types = ["member"]

    remove_values = {f'{user_type}_role': bool(team_map.get(f'remove_{user_type}s', True)) for user_type in user_types}
    all_teams = Team.objects.all().values_list('name', 'organization__name')
    for role, remove_value in remove_values.items():
        if remove_value:
            for team_name, organization_name in all_teams:
                if organization_name not in desired_team_state or team_name not in desired_team_state[organization_name]:
                    desired_team_state[organization_name] = {team_name: {}}
                desired_team_state[organization_name][team_name] = {role: False}

    social_auth_member_scope_values = set(kwargs.get('response', {}).get(social_auth_scope, []))
    for team_name_map in team_map.get('team_org_map', []):
        team_name = team_name_map.get('team', None)
        org_name = team_name_map.get('organization', None)

        if not org_name:
            # Settings field validation should prevent this.
            logger.error(f"organization name invalid for team {team_name}")
            continue

        default_team_scope_value = f'TEAM_{team_name.upper().replace(" ", "_")}_{org_name.upper().replace(" ", "_")}_MEMBER'
        team_member_role = False
        if team_name_map.get('social_auth_member_value', default_team_scope_value) in social_auth_member_scope_values:
            teams_to_create[team_name] = org_name
            team_member_role = True

        if org_name not in desired_team_state:
            desired_team_state[org_name] = {team_name: {}}
        desired_team_state[org_name][team_name] = {'member_role': team_member_role}


def _set_flag(user, response: dict, flag: str):
    '''
    Helper function to set the is_superuser is_system_auditor flags for the OIDC Generic adapter
    '''
    user_flags_settings = settings.SOCIAL_AUTH_OIDC_USER_FLAGS_REMOTE_MAP

    remove_flag = user_flags_settings.get(f"remove_{flag}s", True)
    if remove_flag:
        setattr(user, f"is_{flag}", False)

    # Get the users new flag value
    new_value = user_flags_settings.get(f"is_{flag}_value", None) in response.get(user_flags_settings.get(f"is_{flag}_scope", "roles"), [])

    print(response)
    print(user_flags_settings)
    print(new_value)

    # If the user should not be removed from its role but it has not the role anymore don't set its role
    if not remove_flag and not new_value:
        return

    setattr(user, f"is_{flag}", new_value)


def update_user_flags(backend, details, user=None, *args, **kwargs):
    if not user:
        return
    _set_flag(user, kwargs.get('response', {}), 'superuser')
    _set_flag(user, kwargs.get('response', {}), 'system_auditor')
    user.save()
