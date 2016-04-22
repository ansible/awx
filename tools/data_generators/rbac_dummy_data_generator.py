#!/usr/bin/env python
# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved
import os
import sys
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "awx.settings.development") # noqa

import django
django.setup() # noqa


# Python
from collections import defaultdict
from optparse import make_option, OptionParser


# Django

from django.utils.timezone import now
from django.contrib.auth.models import User
from django.db import transaction

# awx
from awx.main.models import * # noqa




option_list = [
    make_option('--organizations', action='store', type='int', default=3,
                help='Number of organizations to create'),
    make_option('--users', action='store', type='int', default=10,
                help='Number of users to create'),
    make_option('--teams', action='store', type='int', default=5,
                help='Number of teams to create'),
    make_option('--projects', action='store', type='int', default=10,
                help='Number of projects to create'),
    make_option('--job-templates', action='store', type='int', default=20,
                help='Number of job templates to create'),
    make_option('--credentials', action='store', type='int', default=5,
                help='Number of credentials to create'),
    make_option('--inventories', action='store', type='int', default=5,
                help='Number of credentials to create'),
    make_option('--inventory-groups', action='store', type='int', default=10,
                help='Number of credentials to create'),
    make_option('--inventory-hosts', action='store', type='int', default=40,
                help='number of credentials to create'),
    make_option('--jobs', action='store', type='int', default=200,
                help='number of job entries to create'),
    make_option('--job-events', action='store', type='int', default=500,
                help='number of job event entries to create'),
    make_option('--pretend', action='store_true',
                help="Don't commit the data to the database"),
    make_option('--prefix', action='store', type='string', default='',
                help="Prefix generated names with this string"),
    #make_option('--spread-bias', action='store', type='string', default='exponential',
    #            help='"exponential" to bias associations exponentially front loaded for - for ex'),
]
parser = OptionParser(option_list=option_list)
options, remainder = parser.parse_args()
options = vars(options)


n_organizations    = int(options['organizations'])
n_users            = int(options['users'])
n_teams            = int(options['teams'])
n_projects         = int(options['projects'])
n_job_templates    = int(options['job_templates'])
n_credentials      = int(options['credentials'])
n_inventories      = int(options['inventories'])
n_inventory_groups = int(options['inventory_groups'])
n_inventory_hosts  = int(options['inventory_hosts'])
n_jobs             = int(options['jobs'])
n_job_events       = int(options['job_events'])
prefix             = options['prefix']

organizations    = []
users            = []
teams            = []
projects         = []
job_templates    = []
credentials      = []
inventories      = []
inventory_groups = []
inventory_hosts  = []
jobs             = []
#job_events       = []

def spread(n, m):
    ret = []
    # At least one in each slot, split up the rest exponentially so the first
    # buckets contain a lot of entries
    for i in xrange(m):
        if n > 0:
            ret.append(1)
            n -= 1
        else:
            ret.append(0)

    for i in xrange(m):
        n_in_this_slot = n // 2
        n-= n_in_this_slot
        ret[i] += n_in_this_slot
    if n > 0 and len(ret):
        ret[0] += n
    return ret

ids = defaultdict(lambda: 0)


class Rollback(Exception):
    pass


try:

    with transaction.atomic():
        with batch_role_ancestor_rebuilding():
            admin, _      = User.objects.get_or_create(username = 'admin', is_superuser=True)
            org_admin, _  = User.objects.get_or_create(username = 'org_admin')
            org_member, _ = User.objects.get_or_create(username = 'org_member')
            prj_admin, _  = User.objects.get_or_create(username = 'prj_admin')
            jt_admin, _   = User.objects.get_or_create(username = 'jt_admin')
            inv_admin, _  = User.objects.get_or_create(username = 'inv_admin')

            admin.is_superuser = True
            admin.save()
            admin.set_password('test')
            admin.save()
            org_admin.set_password('test')
            org_admin.save()
            org_member.set_password('test')
            org_member.save()
            prj_admin.set_password('test')
            prj_admin.save()
            jt_admin.set_password('test')
            jt_admin.save()
            inv_admin.set_password('test')
            inv_admin.save()



            print('# Creating %d organizations' % n_organizations)
            for i in xrange(n_organizations):
                sys.stdout.write('\r%d     ' % (i + 1))
                sys.stdout.flush()
                org = Organization.objects.create(name='%s Organization %d' % (prefix, i))
                organizations.append(org)
                if i == 0:
                    org.admin_role.members.add(org_admin)
                    org.member_role.members.add(org_admin)
                    org.member_role.members.add(org_member)
                    org.member_role.members.add(prj_admin)
                    org.member_role.members.add(jt_admin)
                    org.member_role.members.add(inv_admin)

            print('')

            print('# Creating %d users' % n_users)
            org_idx = 0
            for n in spread(n_users, n_organizations):
                for i in range(n):
                    ids['user'] += 1
                    user_id = ids['user']
                    sys.stdout.write('\r   Assigning %d to %s: %d     ' % (n, organizations[org_idx].name, i+ 1))
                    sys.stdout.flush()
                    user = User.objects.create(username='%suser-%d' % (prefix, user_id))
                    organizations[org_idx].member_role.members.add(user)
                    users.append(user)
                org_idx += 1
                print('')

            print('# Creating %d teams' % n_teams)
            org_idx = 0
            for n in spread(n_teams, n_organizations):
                org = organizations[org_idx]
                for i in range(n):
                    ids['team'] += 1
                    team_id = ids['team']
                    sys.stdout.write('\r   Assigning %d to %s: %d     ' % (n, org.name, i+ 1))
                    sys.stdout.flush()
                    team = Team.objects.create(name='%s Team %d Org %d' % (prefix, team_id, org_idx), organization=org)
                    teams.append(team)
                org_idx += 1
                print('')

            print('# Adding users to teams')
            for org in organizations:
                org_teams = [t for t in org.teams.all()]
                org_users = [u for u in org.member_role.members.all()]
                print('  Spreading %d users accross %d teams for %s' % (len(org_users), len(org_teams), org.name))
                # Our normal spread for most users
                cur_user_idx = 0
                cur_team_idx = 0
                for n in spread(len(org_users), len(org_teams)):
                    team = org_teams[cur_team_idx]
                    for i in range(n):
                        if cur_user_idx < len(org_users):
                            user = org_users[cur_user_idx]
                            team.member_role.members.add(user)
                        cur_user_idx += 1
                    cur_team_idx += 1

                # First user gets added to all teams
                for team in org_teams:
                    team.member_role.members.add(org_users[0])


            print('# Creating %d credentials for users' % (n_credentials - n_credentials // 2))
            user_idx = 0
            for n in spread(n_credentials - n_credentials // 2, n_users):
                user = users[user_idx]
                for i in range(n):
                    ids['credential'] += 1
                    sys.stdout.write('\r   %d     ' % (ids['credential']))
                    sys.stdout.flush()
                    credential_id = ids['credential']
                    credential = Credential.objects.create(name='%s Credential %d User %d' % (prefix, credential_id, user_idx))
                    credential.owner_role.members.add(user)
                    credentials.append(credential)
                user_idx += 1
            print('')

            print('# Creating %d credentials for teams' % (n_credentials // 2))
            team_idx = 0
            starting_credential_id = ids['credential']
            for n in spread(n_credentials - n_credentials // 2, n_teams):
                team = teams[team_idx]
                for i in range(n):
                    ids['credential'] += 1
                    sys.stdout.write('\r   %d     ' % (ids['credential'] - starting_credential_id))
                    sys.stdout.flush()
                    credential_id = ids['credential']
                    credential = Credential.objects.create(name='%s Credential %d team %d' % (prefix, credential_id, team_idx))
                    credential.owner_role.parents.add(team.member_role)
                    credentials.append(credential)
                team_idx += 1
            print('')

            print('# Creating %d projects' % n_projects)
            org_idx = 0
            for n in spread(n_projects, n_organizations):
                org = organizations[org_idx]
                for i in range(n):
                    ids['project'] += 1
                    project_id = ids['project']
                    sys.stdout.write('\r   Assigning %d to %s: %d     ' % (n, org.name, i+ 1))
                    sys.stdout.flush()
                    project = Project.objects.create(name='%s Project %d Org %d' % (prefix, project_id, org_idx), organization=org)
                    projects.append(project)
                    if org_idx == 0 and i == 0:
                        project.admin_role.members.add(prj_admin)

                org_idx += 1
                print('')


            print('# Creating %d inventories' % n_inventories)
            org_idx = 0
            for n in spread(n_inventories, min(n_inventories // 4 + 1, n_organizations)):
                org = organizations[org_idx]
                for i in range(n):
                    ids['inventory'] += 1
                    inventory_id = ids['inventory']
                    sys.stdout.write('\r   Assigning %d to %s: %d     ' % (n, org.name, i+ 1))
                    sys.stdout.flush()
                    inventory = Inventory.objects.create(name='%s Inventory %d Org %d' % (prefix, inventory_id, org_idx), organization=org)
                    inventories.append(inventory)
                    if org_idx == 0 and i == 0:
                        inventory.admin_role.members.add(inv_admin)

                org_idx += 1
                print('')


            print('# Creating %d inventory_groups' % n_inventory_groups)
            inv_idx = 0
            for n in spread(n_inventory_groups, n_inventories):
                inventory = inventories[inv_idx]
                parent_list = [None] * 3
                for i in range(n):
                    ids['group'] += 1
                    group_id = ids['group']
                    sys.stdout.write('\r   Assigning %d to %s: %d     ' % (n, inventory.name, i+ 1))
                    sys.stdout.flush()
                    group = Group.objects.create(
                        name='%s Group %d Inventory %d' % (prefix, group_id, inv_idx),
                        inventory=inventory,
                    )
                    # Have each group have up to 3 parent groups
                    for parent_n in range(3):
                        if i // 4 + parent_n < len(parent_list) and parent_list[i // 4 + parent_n]:
                            group.parents.add(parent_list[i // 4 + parent_n])
                    if parent_list[i // 4] is None:
                        parent_list[i // 4] = group
                    else:
                        parent_list.append(group)
                    inventory_groups.append(group)

                inv_idx += 1
                print('')


            print('# Creating %d inventory_hosts' % n_inventory_hosts)
            group_idx = 0
            for n in spread(n_inventory_hosts, n_inventory_groups):
                group = inventory_groups[group_idx]
                for i in range(n):
                    ids['host'] += 1
                    host_id = ids['host']
                    sys.stdout.write('\r   Assigning %d to %s: %d     ' % (n, group.name, i+ 1))
                    sys.stdout.flush()
                    host = Host.objects.create(name='%s.host-%06d.group-%05d.dummy' % (prefix, host_id, group_idx), inventory=group.inventory)
                    # Add the host to up to 3 groups
                    host.groups.add(group)
                    for m in range(2):
                        if group_idx + m < len(inventory_groups) and group.inventory.id == inventory_groups[group_idx + m].inventory.id:
                            host.groups.add(inventory_groups[group_idx + m])

                    inventory_hosts.append(host)

                group_idx += 1
                print('')

            print('# Creating %d job_templates' % n_job_templates)
            project_idx = 0
            inv_idx = 0
            for n in spread(n_job_templates, n_projects):
                project = projects[project_idx]
                for i in range(n):
                    ids['job_template'] += 1
                    job_template_id = ids['job_template']
                    sys.stdout.write('\r   Assigning %d to %s: %d     ' % (n, project.name, i+ 1))
                    sys.stdout.flush()

                    inventory = None
                    org_inv_count = project.organization.inventories.count()
                    if org_inv_count > 0:
                        inventory = project.organization.inventories.all()[inv_idx % org_inv_count]

                    job_template = JobTemplate.objects.create(
                        name='%s Job Template %d Project %d' % (prefix, job_template_id, project_idx),
                        inventory=inventory,
                        project=project,
                    )
                    job_templates.append(job_template)
                    inv_idx += 1
                    if project_idx == 0 and i == 0:
                        job_template.admin_role.members.add(jt_admin)
                project_idx += 1
                print('')

            print('# Creating %d jobs' % n_jobs)
            group_idx = 0
            job_template_idx = 0
            for n in spread(n_jobs, n_job_templates):
                job_template = job_templates[job_template_idx]
                for i in range(n):
                    sys.stdout.write('\r   Assigning %d to %s: %d     ' % (n, job_template.name, i+ 1))
                    sys.stdout.flush()
                    job = Job.objects.create(job_template=job_template)
                    jobs.append(job)

                    if job_template.inventory:
                        inv_groups = [g for g in job_template.inventory.groups.all()]
                        if len(inv_groups):
                            JobHostSummary.objects.bulk_create([
                                JobHostSummary(
                                    job=job, host=h, host_name=h.name, processed=1,
                                    created=now(), modified=now()
                                )
                                for h in inv_groups[group_idx % len(inv_groups)].hosts.all()[:100]
                            ])
                    group_idx += 1
                job_template_idx += 1
                if n:
                    print('')

            print('# Creating %d job events' % n_job_events)
            job_idx = 0
            for n in spread(n_job_events, n_jobs):
                job = jobs[job_idx]
                sys.stdout.write('\r   Creating %d job events for job %d' % (n, job.id))
                sys.stdout.flush()
                JobEvent.objects.bulk_create([
                    JobEvent(
                        created=now(),
                        modified=now(),
                        job=job,
                        event='runner_on_ok'
                    )
                    for i in range(n)
                ])
                job_idx += 1
                if n:
                    print('')

        if options['pretend']:
            raise Rollback()
except Rollback:
    print('Rolled back changes')
    pass
