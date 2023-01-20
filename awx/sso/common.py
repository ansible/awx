# Copyright (c) 2022 Ansible, Inc.
# All Rights Reserved.

import logging

from django.contrib.contenttypes.models import ContentType
from django.db.utils import IntegrityError
from awx.main.models import Organization, Team

logger = logging.getLogger('awx.sso.common')


def get_orgs_by_ids():
    existing_orgs = {}
    for (org_id, org_name) in Organization.objects.all().values_list('id', 'name'):
        existing_orgs[org_name] = org_id
    return existing_orgs


def reconcile_users_org_team_mappings(user, desired_org_states, desired_team_states, source):
    #
    # Arguments:
    #   user - a user object
    #   desired_org_states: { '<org_name>': { '<role>': <boolean> or None } }
    #   desired_team_states: { '<org_name>': { '<team name>': { '<role>': <boolean> or None } } }
    #   source - a text label indicating the "authentication adapter" for debug messages
    #
    # This function will load the users existing roles and then based on the desired states modify the users roles
    #    True indicates the user needs to be a member of the role
    #    False indicates the user should not be a member of the role
    #    None means this function should not change the users membership of a role
    #

    content_types = []
    reconcile_items = []
    if desired_org_states:
        content_types.append(ContentType.objects.get_for_model(Organization))
        reconcile_items.append(('organization', desired_org_states))
    if desired_team_states:
        content_types.append(ContentType.objects.get_for_model(Team))
        reconcile_items.append(('team', desired_team_states))

    if not content_types:
        # If both desired states were empty we can simply return because there is nothing to reconcile
        return

    # users_roles is a flat set of IDs
    users_roles = set(user.roles.filter(content_type__in=content_types).values_list('pk', flat=True))

    for object_type, desired_states in reconcile_items:
        roles = []
        # Get a set of named tuples for the org/team name plus all of the roles we got above
        if object_type == 'organization':
            for sub_dict in desired_states.values():
                for role_name in sub_dict:
                    if sub_dict[role_name] is None:
                        continue
                    if role_name not in roles:
                        roles.append(role_name)
            model_roles = Organization.objects.filter(name__in=desired_states.keys()).values_list('name', *roles, named=True)
        else:
            team_names = []
            for teams_dict in desired_states.values():
                team_names.extend(teams_dict.keys())
                for sub_dict in teams_dict.values():
                    for role_name in sub_dict:
                        if sub_dict[role_name] is None:
                            continue
                        if role_name not in roles:
                            roles.append(role_name)
            model_roles = Team.objects.filter(name__in=team_names).values_list('name', 'organization__name', *roles, named=True)

        for row in model_roles:
            for role_name in roles:
                if object_type == 'organization':
                    desired_state = desired_states.get(row.name, {})
                else:
                    desired_state = desired_states.get(row.organization__name, {}).get(row.name, {})

                if desired_state.get(role_name, None) is None:
                    # The mapping was not defined for this [org/team]/role so we can just pass
                    continue

                # If somehow the auth adapter knows about an items role but that role is not defined in the DB we are going to print a pretty error
                # This is your classic safety net that we should never hit; but here you are reading this comment... good luck and Godspeed.
                role_id = getattr(row, role_name, None)
                if role_id is None:
                    logger.error("{} adapter wanted to manage role {} of {} {} but that role is not defined".format(source, role_name, object_type, row.name))
                    continue

                if desired_state[role_name]:
                    # The desired state was the user mapped into the object_type, if the user was not mapped in map them in
                    if role_id not in users_roles:
                        logger.debug("{} adapter adding user {} to {} {} as {}".format(source, user.username, object_type, row.name, role_name))
                        user.roles.add(role_id)
                else:
                    # The desired state was the user was not mapped into the org, if the user has the permission remove it
                    if role_id in users_roles:
                        logger.debug("{} adapter removing user {} permission of {} from {} {}".format(source, user.username, role_name, object_type, row.name))
                        user.roles.remove(role_id)


def create_org_and_teams(org_list, team_map, adapter, can_create=True):
    #
    # org_list is a set of organization names
    # team_map is a dict of {<team_name>: <org name>}
    #
    # Move this junk into save of the settings for performance later, there is no need to do that here
    #    with maybe the exception of someone defining this in settings before the server is started?
    # ==============================================================================================================

    if not can_create:
        logger.debug(f"Adapter {adapter} is not allowed to create orgs/teams")
        return

    # Get all of the IDs and names of orgs in the DB and create any new org defined in LDAP that does not exist in the DB
    existing_orgs = get_orgs_by_ids()

    # Parse through orgs and teams provided and create a list of unique items we care about creating
    all_orgs = list(set(org_list))
    all_teams = []
    for team_name in team_map:
        org_name = team_map[team_name]
        if org_name:
            if org_name not in all_orgs:
                all_orgs.append(org_name)
            # We don't have to test if this is in all_teams because team_map is already a hash
            all_teams.append(team_name)
        else:
            # The UI should prevent this condition so this is just a double check to prevent a stack trace....
            #  although the rest of the login process might stack later on
            logger.error("{} adapter is attempting to create a team {} but it does not have an org".format(adapter, team_name))

    for org_name in all_orgs:
        if org_name and org_name not in existing_orgs:
            logger.info("{} adapter is creating org {}".format(adapter, org_name))
            try:
                new_org = get_or_create_org_with_default_galaxy_cred(name=org_name)
            except IntegrityError:
                # Another thread must have created this org before we did so now we need to get it
                new_org = get_or_create_org_with_default_galaxy_cred(name=org_name)
            # Add the org name to the existing orgs since we created it and we may need it to build the teams below
            existing_orgs[org_name] = new_org.id

    # Do the same for teams
    existing_team_names = list(Team.objects.all().values_list('name', flat=True))
    for team_name in all_teams:
        if team_name not in existing_team_names:
            logger.info("{} adapter is creating team {} in org {}".format(adapter, team_name, team_map[team_name]))
            try:
                Team.objects.create(name=team_name, organization_id=existing_orgs[team_map[team_name]])
            except IntegrityError:
                # If another process got here before us that is ok because we don't need the ID from this team or anything
                pass
    # End move some day
    # ==============================================================================================================


def get_or_create_org_with_default_galaxy_cred(**kwargs):
    from awx.main.models import Organization, Credential

    (org, org_created) = Organization.objects.get_or_create(**kwargs)
    if org_created:
        logger.debug("Created org {} (id {}) from {}".format(org.name, org.id, kwargs))
        public_galaxy_credential = Credential.objects.filter(managed=True, name='Ansible Galaxy').first()
        if public_galaxy_credential is not None:
            org.galaxy_credentials.add(public_galaxy_credential)
            logger.debug("Added default Ansible Galaxy credential to org")
        else:
            logger.debug("Could not find default Ansible Galaxy credential to add to org")
    return org
