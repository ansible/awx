# Copyright (c) 2022 Ansible, Inc.
# All Rights Reserved.

import logging

from django.contrib.contenttypes.models import ContentType
from awx.main.models import Organization, Team

logger = logging.getLogger('awx.sso.common')


def reconcile_users_org_team_mappings(user, desired_org_states, desired_team_states, source):
    #
    # desired_org_states:
    #   dict of org names whose value is a dict of roles (i.e. admin-role) set to booleans
    #
    # desired_team_states:
    #   dict of team names whose value is a dict of roles (i.e. member_role) set to booleans
    #

    content_types = []
    reconcile_items = []
    if desired_org_states:
        content_types.append(ContentType.objects.get_for_model(Organization))
        reconcile_items.append(('organization', desired_org_states, Organization))
    if desired_team_states:
        content_types.append(ContentType.objects.get_for_model(Team))
        reconcile_items.append(('team', desired_team_states, Team))

    if not content_types:
        # If both desired states were empty we can simply return because there is nothing to reconcile
        return

    # users_roles is a flat set of IDs
    users_roles = set(user.roles.filter(content_type__in=content_types).values_list('pk', flat=True))

    for object_type, desired_states, model in reconcile_items:
        # Get all of the roles in the desired states for efficient DB extraction
        roles = []
        for sub_dict in desired_states.values():
            for role_name in sub_dict:
                if sub_dict[role_name] is None:
                    continue
                if role_name not in roles:
                    roles.append(role_name)

        # Get a set of named tuples for the org/team name plus all of the roles we got above
        model_roles = model.objects.filter(name__in=desired_states.keys()).values_list('name', *roles, named=True)
        for row in model_roles:
            for role_name in roles:
                desired_state = desired_states.get(row.name, {})
                if desired_state[role_name] is None:
                    # The mapping was not defined for this [org/team]/role so we can just pass
                    pass

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
