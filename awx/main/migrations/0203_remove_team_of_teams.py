import logging

from django.db import migrations

logger = logging.getLogger('awx.main.migrations')


def consolidate_indirect_user_roles(apps, schema_editor):
    """
    A user should have a member role for every team they were indirectly
    a member of. ex. Team A is a member of Team B. All users in Team A
    previously were only members of Team A. They should now be members of
    Team A and Team B.
    """

    # get object roles for membership on teams
    ObjectRole = apps.get_model('dab_rbac', 'ObjectRole')
    team_member_object_roles = ObjectRole.objects.filter(content_type__model='team').filter(
        role_definition__description='Has member permissions to a single team'
    )

    # for team member object role, check if teams are assigned
    for obj_role in team_member_object_roles:
        obj_role_team_id = obj_role.object_id
        incl_teams = obj_role.teams.all()
        if incl_teams:
            # search for all indirect parents of this team
            all_parents = {obj_role_team_id}
            working_parents_set = {obj_role_team_id}
            check_parents = True

            while check_parents == True:
                new_parents = set()
                for parent_id in working_parents_set:
                    parent_team_roles = list(team_member_object_roles.filter(teams__id=parent_id).values_list('object_id', flat=True))
                    if parent_team_roles:
                        new_parents.update(parent_team_roles)
                if not new_parents:
                    check_parents = False
                else:
                    all_parents.update(new_parents)
                    working_parents_set.clear()
                    working_parents_set.update(new_parents)

            # add child team users to all of the discovered parent team object roles
            for team in incl_teams:
                team_users = team_member_object_roles.get(object_id=team.id).users.all()

                for parent_id in all_parents:
                    parent_obj_role = team_member_object_roles.get(object_id=parent_id)
                    for user in team_users:
                        parent_obj_role.users.add(user.id)

                # remove team from object role
                obj_role.teams.remove(team.id)


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0202_squashed_deletions'),
    ]

    operations = [migrations.RunPython(consolidate_indirect_user_roles, migrations.RunPython.noop)]
