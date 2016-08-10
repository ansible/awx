# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from awx.main.migrations import _rbac as rbac
from awx.main.migrations import _migration_utils as migration_utils
from django.db.models import Q
from django.db import migrations


def synchronize_role_changes(apps, schema_editor):
    # The implicit parent roles have been updated for Credential.read_role and
    # Team.read_role so these saves will pickup those changes and fix things up.
    Team = apps.get_model('main', 'Team')
    Credential = apps.get_model('main', 'Credential')

    for credential in Credential.objects.iterator():
        credential.save()
    for team in Team.objects.iterator():
        team.save()

def populate_credential_teams_field(apps, schema_editor):
    Team = apps.get_model('main', 'Team')
    Credential = apps.get_model('main', 'Credential')

    for credential in Credential.objects.iterator():
        teams_qs = Team.objects.filter(
            Q(member_role__children=credential.use_role) |
            Q(member_role__children=credential.admin_role)
        )
        for team in teams_qs.iterator():
            credential.teams.add(team)

class Migration(migrations.Migration):

    dependencies = [
        ('main', '0030_audit_team_credential_changes'),
    ]

    operations = [
        migrations.RunPython(migration_utils.set_current_apps_for_migrations),
        migrations.RunPython(synchronize_role_changes),
        migrations.RunPython(populate_credential_teams_field),
        migrations.RunPython(rbac.rebuild_role_hierarchy),
    ]
