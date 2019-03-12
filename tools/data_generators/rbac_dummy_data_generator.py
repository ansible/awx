#!/usr/bin/env python
# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved
import os
import sys

# Python
from collections import defaultdict
from optparse import make_option, OptionParser
from datetime import datetime
import logging


# Django
import django
from django.utils.timezone import now


base_dir = os.path.abspath(  # Convert into absolute path string
    os.path.join(  # Current file's grandparent directory
        os.path.join(  # Current file's parent directory
            os.path.dirname(  # Current file's directory
                os.path.abspath(__file__)  # Current file path
            ),
            os.pardir
        ),
        os.pardir
    )
)

if base_dir not in sys.path:
    sys.path.insert(1, base_dir)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "awx.settings.development") # noqa
django.setup() # noqa


from django.db import transaction # noqa

# awx
from awx.main.models import (  # noqa
    Credential, CredentialType, Group, Host, Inventory, Job, JobEvent,
    JobHostSummary, JobTemplate, Label, Organization, PrimordialModel, Project,
    Team, User, WorkflowJobTemplate, WorkflowJobTemplateNode,
    batch_role_ancestor_rebuilding,
)

from awx.main.signals import ( # noqa
    disable_activity_stream,
    disable_computed_fields
)


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
    make_option('--wfjts', action='store', type='int', default=15,
                help='number of workflow job templates to create'),
    make_option('--nodes', action='store', type='int', default=200,
                help='number of workflow job template nodes to create'),
    make_option('--labels', action='store', type='int', default=100,
                help='labels to create, will associate 10x as many'),
    make_option('--jobs', action='store', type='int', default=200,
                help='number of job entries to create'),
    make_option('--job-events', action='store', type='int', default=500,
                help='number of job event entries to create'),
    make_option('--pretend', action='store_true',
                help="Don't commit the data to the database"),
    make_option('--preset', action='store', type='string', default='',
                help="Preset data set to use"),
    make_option('--prefix', action='store', type='string', default='',
                help="Prefix generated names with this string"),
    #make_option('--spread-bias', action='store', type='string', default='exponential',
    #            help='"exponential" to bias associations exponentially front loaded for - for ex'),
]
parser = OptionParser(option_list=option_list)
options, remainder = parser.parse_args()
options = vars(options)


if options['preset']:
    print(' Using preset data numbers set ' + str(options['preset']))
    # Read the numbers of resources from presets file, if provided
    presets_filename = os.path.abspath(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'presets.tsv'))

    with open(presets_filename) as f:
        text = f.read()

    split_lines = [line.split('\t') for line in text.split('\n')]
    keys = split_lines[0][1:]

    try:
        col = keys.index(options['preset'])
    except ValueError:
        raise Exception('Preset "%s" dataset not found, options are %s' % (options['preset'], keys))

    options.update({cols[0]: cols[col + 1] for cols in split_lines})

    if not options['prefix']:
        options['prefix'] = options['preset']


n_organizations    = int(options['organizations'])
n_users            = int(options['users'])
n_teams            = int(options['teams'])
n_projects         = int(options['projects'])
n_job_templates    = int(options['job_templates'])
n_credentials      = int(options['credentials'])
n_inventories      = int(options['inventories'])
n_inventory_groups = int(options['inventory_groups'])
n_inventory_hosts  = int(options['inventory_hosts'])
n_wfjts            = int(options['wfjts'])
n_nodes            = int(options['nodes'])
n_labels           = int(options['labels'])
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
wfjts            = []
nodes            = []
labels           = []
jobs             = []
#job_events       = []


def spread(n, m):
    ret = []
    # At least one in each slot, split up the rest exponentially so the first
    # buckets contain a lot of entries
    for i in range(m):
        if n > 0:
            ret.append(1)
            n -= 1
        else:
            ret.append(0)

    for i in range(m):
        n_in_this_slot = n // 2
        n-= n_in_this_slot
        ret[i] += n_in_this_slot
    if n > 0 and len(ret):
        ret[0] += n
    return ret


ids = defaultdict(lambda: 0)
bulk_data_description = 'From Tower bulk-data script'


# function to cycle through a list
def yield_choice(alist):
    ix = 0
    while True:
        yield alist[ix]
        ix += 1
        if ix >= len(alist):
            ix = 0


class Rollback(Exception):
    pass


# Normally the modified_by field is populated by the crum library automatically,
# but since this is ran outside the request-response cycle that won't work.
# It is disaled here.
def mock_save(self, *args, **kwargs):
    return super(PrimordialModel, self).save(*args, **kwargs)


def mock_update(self):
    return


def mock_computed_fields(self, **kwargs):
    pass


PrimordialModel.save = mock_save
Project.update = mock_update

startTime = datetime.now()


def make_the_data():
    with disable_activity_stream():
        with batch_role_ancestor_rebuilding(), disable_computed_fields():
            admin, created      = User.objects.get_or_create(username = 'admin', is_superuser=True)
            if created:
                admin.is_superuser = True
                admin.save()
                admin.set_password('test')
                admin.save()

            org_admin, created  = User.objects.get_or_create(username = 'org_admin')
            if created:
                org_admin.set_password('test')
                org_admin.save()

            org_member, created = User.objects.get_or_create(username = 'org_member')
            if created:
                org_member.set_password('test')
                org_member.save()

            prj_admin, created  = User.objects.get_or_create(username = 'prj_admin')
            if created:
                prj_admin.set_password('test')
                prj_admin.save()

            jt_admin, created   = User.objects.get_or_create(username = 'jt_admin')
            if created:
                jt_admin.set_password('test')
                jt_admin.save()

            inv_admin, created  = User.objects.get_or_create(username = 'inv_admin')
            if created:
                inv_admin.set_password('test')
                inv_admin.save()


            print('# Creating %d organizations' % n_organizations)
            for i in range(n_organizations):
                sys.stdout.write('\r%d     ' % (i + 1))
                sys.stdout.flush()
                org, _ = Organization.objects.get_or_create(name='%s Organization %d' % (prefix, i))
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
                    user, _ = User.objects.get_or_create(username='%suser-%d' % (prefix, user_id))
                    organizations[org_idx].member_role.members.add(user)
                    users.append(user)
                org_idx += 1
                print('')

            creator_gen = yield_choice(users)
            for i in range(6):
                next(creator_gen)
            modifier_gen = yield_choice(users)

            print('# Creating %d teams' % n_teams)
            org_idx = 0
            for n in spread(n_teams, n_organizations):
                org = organizations[org_idx]
                for i in range(n):
                    ids['team'] += 1
                    team_id = ids['team']
                    sys.stdout.write('\r   Assigning %d to %s: %d     ' % (n, org.name, i+ 1))
                    sys.stdout.flush()
                    team, _ = Team.objects.get_or_create(
                        name='%s Team %d Org %d' % (prefix, team_id, org_idx), organization=org,
                        defaults=dict(created_by=next(creator_gen),
                                      modified_by=next(modifier_gen))
                    )
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
                    credential, _ = Credential.objects.get_or_create(
                        name='%s Credential %d User %d' % (prefix, credential_id, user_idx),
                        defaults=dict(created_by=next(creator_gen),
                                      modified_by=next(modifier_gen)),
                        credential_type=CredentialType.objects.filter(namespace='ssh').first()
                    )
                    credential.admin_role.members.add(user)
                    credentials.append(credential)
                user_idx += 1
            print('')

            credential_gen = yield_choice(credentials)

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
                    credential, _ = Credential.objects.get_or_create(
                        name='%s Credential %d team %d' % (prefix, credential_id, team_idx),
                        defaults=dict(created_by=next(creator_gen),
                                      modified_by=next(modifier_gen)),
                        credential_type=CredentialType.objects.filter(namespace='ssh').first()
                    )
                    credential.admin_role.parents.add(team.member_role)
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
                    project, _ = Project.objects.get_or_create(
                        name='%s Project %d Org %d' % (prefix, project_id, org_idx),
                        organization=org,
                        defaults=dict(
                            created_by=next(creator_gen), modified_by=next(modifier_gen),
                            scm_url='https://github.com/ansible/test-playbooks.git',
                            scm_type='git',
                            playbook_files=[
                                "check.yml", "debug-50.yml", "debug.yml", "debug2.yml",
                                "debug_extra_vars.yml", "dynamic_inventory.yml",
                                "environ_test.yml", "fail_unless.yml", "pass_unless.yml",
                                "pause.yml", "ping-20.yml", "ping.yml",
                                "setfact_50.yml", "vault.yml"
                            ])
                    )
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
                    inventory, _ = Inventory.objects.get_or_create(
                        name='%s Inventory %d Org %d' % (prefix, inventory_id, org_idx),
                        organization=org,
                        defaults=dict(created_by=next(creator_gen),
                                      modified_by=next(modifier_gen)),
                        variables='{"ansible_connection": "local"}'
                    )
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
                    group, _ = Group.objects.get_or_create(
                        name='%s Group %d Inventory %d' % (prefix, group_id, inv_idx),
                        inventory=inventory,
                        defaults=dict(created_by=next(creator_gen),
                                      modified_by=next(modifier_gen))
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
                    host, _ = Host.objects.get_or_create(
                        name='%s.host-%06d.group-%05d.dummy' % (prefix, host_id, group_idx),
                        inventory=group.inventory,
                        defaults=dict(created_by=next(creator_gen),
                                      modified_by=next(modifier_gen))
                    )
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
                    extra_kwargs = {}

                    job_template, _ = JobTemplate.objects.get_or_create(
                        name='%s Job Template %d Project %d' % (prefix, job_template_id, project_idx),
                        defaults=dict(
                            inventory=inventory,
                            project=project,
                            created_by=next(creator_gen),
                            modified_by=next(modifier_gen),
                            playbook="debug.yml",
                            **extra_kwargs)
                    )
                    job_template.credentials.add(next(credential_gen))
                    if ids['job_template'] % 7 == 0:
                        job_template.credentials.add(next(credential_gen))
                    if ids['job_template'] % 5 == 0:  # formerly cloud credential
                        job_template.credentials.add(next(credential_gen))
                    job_template._is_new = _
                    job_templates.append(job_template)
                    inv_idx += 1
                    if project_idx == 0 and i == 0:
                        job_template.admin_role.members.add(jt_admin)
                project_idx += 1
                if n > 0:
                    print('')

            print('# Creating %d Workflow Job Templates' % n_wfjts)
            org_idx = 0
            for n in spread(n_wfjts, n_organizations):
                org = organizations[org_idx]
                for i in range(n):
                    ids['wfjts'] += 1
                    wfjt_id = ids['wfjts']
                    sys.stdout.write('\r   Assigning %d to %s: %d     ' % (n, org.name, i+ 1))
                    sys.stdout.flush()
                    wfjt, _ = WorkflowJobTemplate.objects.get_or_create(
                        name='%s WFJT %d Org %d' % (prefix, wfjt_id, org_idx),
                        description=bulk_data_description,
                        organization=org,
                        defaults=dict(created_by=next(creator_gen),
                                      modified_by=next(modifier_gen))
                    )
                    wfjt._is_new = _
                    wfjts.append(wfjt)
                org_idx += 1
                if n:
                    print('')

            print('# Creating %d Workflow Job Template nodes' % n_nodes)
            wfjt_idx = 0
            for n in spread(n_nodes, n_wfjts):
                wfjt = wfjts[wfjt_idx]
                if not wfjt._is_new:
                    continue
                jt_gen = yield_choice(job_templates)
                inv_gen = yield_choice(inventories)
                cred_gen = yield_choice(credentials)
                parent_idx = 0
                wfjt_nodes = []
                for i in range(n):
                    ids['nodes'] += 1
                    sys.stdout.write('\r   Assigning %d to %s: %d     ' % (n, wfjt.name, i+ 1))
                    sys.stdout.flush()
                    kwargs = dict(
                        workflow_job_template=wfjt,
                        unified_job_template=next(jt_gen),
                        modified=now()
                    )
                    if i % 2 == 0:
                        # only apply inventories for every other node
                        kwargs['inventory'] = next(inv_gen)
                    node, _ = WorkflowJobTemplateNode.objects.get_or_create(
                        **kwargs
                    )
                    if i % 3 == 0:
                        # only apply prompted credential every 3rd node
                        node.credentials.add(next(cred_gen))
                    # nodes.append(node)
                    wfjt_nodes.append(node)
                    if i <= 3:
                        continue
                    parent_node = wfjt_nodes[parent_idx]
                    if parent_node.workflow_job_template != node.workflow_job_template:
                        raise Exception("Programming error, associating nodes in different workflows")
                    elif parent_node == node:
                        raise Exception("error, self association")
                    if parent_idx % 2 == 0:
                        parent_node.always_nodes.add(node)
                    else:
                        if (i + 1) % 3 == 0:
                            parent_node.failure_nodes.add(node)
                        else:
                            parent_node.success_nodes.add(node)
                    parent_idx = (parent_idx + 7) % len(wfjt_nodes)
                wfjt_idx += 1
                if n:
                    print('')

            print('# Creating %d Labels' % n_labels)
            org_idx = 0
            for n in spread(n_labels, n_organizations):
                org = organizations[org_idx]
                for i in range(n):
                    ids['labels'] += 1
                    label_id = ids['labels']
                    sys.stdout.write('\r   Assigning %d to %s: %d     ' % (n, org.name, i + 1))
                    sys.stdout.flush()
                    label, _ = Label.objects.get_or_create(
                        name='%sL_%do%d' % (prefix, label_id, org_idx),
                        organization=org,
                        defaults=dict(created_by=next(creator_gen),
                                      modified_by=next(modifier_gen))
                    )
                    labels.append(label)
                org_idx += 1
                if n:
                    print('')
            label_gen = yield_choice(labels)

            print('# Adding labels to job templates')
            jt_idx = 0
            for n in spread(n_labels * 7, n_job_templates):
                if n == 0:
                    continue
                jt = job_templates[jt_idx]
                if not jt._is_new:
                    continue
                print('  Giving %d labels to %s JT' % (n, jt.name))
                for i in range(n):
                    jt.labels.add(next(label_gen))
                jt_idx += 1

            print('# Adding labels to workflow job templates')
            wfjt_idx = 0
            for n in spread(n_labels * 3, n_wfjts):
                wfjt = wfjts[wfjt_idx]
                if not jt._is_new:
                    continue
                print('  Giving %d labels to %s WFJT' % (n, wfjt.name))
                for i in range(n):
                    wfjt.labels.add(next(label_gen))
                wfjt_idx += 1

            # Disable logging here, because it will mess up output format
            logger = logging.getLogger('awx.main')
            logger.propagate = False

            print('# Creating %d jobs' % n_jobs)
            group_idx = 0
            job_template_idx = 0
            job_i = 0
            for n in spread(n_jobs, n_job_templates):
                job_template = job_templates[job_template_idx]
                for i in range(n):
                    sys.stdout.write('\r   Assigning %d to %s: %d     ' % (n, job_template.name, i+ 1))
                    sys.stdout.flush()
                    if len(jobs) % 4 == 0:
                        job_stat = 'failed'
                    elif len(jobs) % 11 == 0:
                        job_stat = 'canceled'
                    else:
                        job_stat = 'successful'
                    job, _ = Job.objects.get_or_create(
                        job_template=job_template,
                        status=job_stat, name="%s-%d" % (job_template.name, job_i),
                        project=job_template.project, inventory=job_template.inventory,
                    )
                    for ec in job_template.credentials.all():
                        job.credentials.add(ec)
                    job._is_new = _
                    jobs.append(job)
                    job_i += 1
                    if not job._is_new:
                        group_idx += 1
                        continue
                    if i + 1 == n:
                        job_template.last_job = job
                        if job_template.pk % 5 == 0:
                            job_template.current_job = job
                        job_template.save()

                    if job._is_new:
                        with transaction.atomic():
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
                # Check if job already has events, for idempotence
                if not job._is_new:
                    continue
                # Bulk create in chunks with maximum chunk size
                MAX_BULK_CREATE = 100
                for j in range((n // MAX_BULK_CREATE) + 1):
                    n_subgroup = MAX_BULK_CREATE
                    if j == n / MAX_BULK_CREATE:
                        # on final pass, create the remainder
                        n_subgroup = n % MAX_BULK_CREATE
                    sys.stdout.write('\r   Creating %d job events for job %d, subgroup: %d' % (n, job.id, j + 1))
                    sys.stdout.flush()
                    JobEvent.objects.bulk_create([
                        JobEvent(
                            created=now(),
                            modified=now(),
                            job=job,
                            event='runner_on_ok'
                        )
                        for i in range(n_subgroup)
                    ])
                job_idx += 1
                if n:
                    print('')


if options['pretend']:
    with transaction.atomic():
        try:
            make_the_data()
            raise Rollback()
        except Rollback:
            print('Rolled back changes')
            pass

else:
    make_the_data()


print('')
print('script execution time: {}'.format(datetime.now() - startTime))
