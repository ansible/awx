from django.contrib.auth.models import User


from awx.main.models import (
    Organization,
    Project,
    Team,
    NotificationTemplate,
    Credential,
    Inventory,
    Job,
    Label,
    WorkflowJobTemplateNode,
)

from .objects import (
    generate_objects,
    generate_role_objects,
    _Mapped,
)

from .fixtures import (
    mk_instance,
    mk_instance_group,
    mk_organization,
    mk_team,
    mk_user,
    mk_job_template,
    mk_job,
    mk_credential,
    mk_inventory,
    mk_project,
    mk_label,
    mk_notification_template,
    mk_workflow_job_template,
)


def apply_roles(roles, objects, persisted):
    '''apply_roles evaluates a list of Role relationships represented as strings.
    The format of this string is 'role:[user|role]'. When a user is provided, they will be
    made a member of the role on the LHS. When a role is provided that role will be added to
    the children of the role on the LHS.

    This function assumes that objects is a dictionary that contains a unique set of key to value
    mappings for all possible "Role objects". See the example below:

        Mapping Users
        -------------
        roles = ['org1.admin_role:user1', 'team1.admin_role:user1']
        objects = {'org1': Organization, 'team1': Team, 'user1': User]

        Mapping Roles
        -------------
        roles = ['org1.admin_role:team1.admin_role']
        objects = {'org1': Organization, 'team1': Team}

        Invalid Mapping
        ---------------
        roles = ['org1.admin_role:team1.admin_role']
        objects = {'org1': Organization', 'user1': User} # Exception, no team1 entry
    '''
    if roles is None:
        return None

    if not persisted:
        raise RuntimeError('roles cannot be used when persisted=False')

    for role in roles:
        obj_role, sep, member_role = role.partition(':')
        if not member_role:
            raise RuntimeError('you must provide an assignment role, got None')

        obj_str, o_role_str = obj_role.split('.')
        member_str, m_sep, m_role_str = member_role.partition('.')

        obj = objects[obj_str]
        obj_role = getattr(obj, o_role_str)

        member = objects[member_str]
        if m_role_str:
            if hasattr(member, m_role_str):
                member_role = getattr(member, m_role_str)
                obj_role.children.add(member_role)
            else:
                raise RuntimeError('unable to find {} role for {}'.format(m_role_str, member_str))
        else:
            if type(member) is User:
                obj_role.members.add(member)
            else:
                raise RuntimeError('unable to add non-user {} for members list of {}'.format(member_str, obj_str))


def generate_users(organization, teams, superuser, persisted, **kwargs):
    '''generate_users evaluates a mixed list of User objects and strings.
    If a string is encountered a user with that username is created and added to the lookup dict.
    If a User object is encountered the User.username is used as a key for the lookup dict.

    A short hand for assigning a user to a team is available in the following format: "team_name:username".
    If a string in that format is encounted an attempt to lookup the team by the key team_name from the teams
    argumnent is made, a KeyError will be thrown if the team does not exist in the dict. The teams argument should
    be a dict of {Team.name:Team}
    '''
    users = {}
    key = 'superusers' if superuser else 'users'
    if key in kwargs and kwargs.get(key) is not None:
        for u in kwargs[key]:
            if type(u) is User:
                users[u.username] = u
            else:
                p1, sep, p2 = u.partition(':')
                if p2:
                    t = teams[p1]
                    users[p2] = mk_user(p2, organization=organization, team=t, is_superuser=superuser, persisted=persisted)
                else:
                    users[p1] = mk_user(p1, organization=organization, team=None, is_superuser=superuser, persisted=persisted)
    return users


def generate_teams(organization, persisted, **kwargs):
    '''generate_teams evalutes a mixed list of Team objects and strings.
    If a string is encountered a team with that string name is created and added to the lookup dict.
    If a Team object is encounted the Team.name is used as a key for the lookup dict.
    '''
    teams = {}
    if 'teams' in kwargs and kwargs.get('teams') is not None:
        for t in kwargs['teams']:
            if type(t) is Team:
                teams[t.name] = t
            else:
                teams[t] = mk_team(t, organization=organization, persisted=persisted)
    return teams


def create_instance(name, instance_groups=None):
    return mk_instance(hostname=name)


def create_instance_group(name, instances=None, minimum=0, percentage=0):
    return mk_instance_group(name=name, instance=instances, minimum=minimum, percentage=percentage)


def create_survey_spec(variables=None, default_type='integer', required=True, min=None, max=None):
    '''
    Returns a valid survey spec for a job template, based on the input
    argument specifying variable name(s)
    '''
    if isinstance(variables, list):
        vars_list = variables
    else:
        vars_list = [variables]
    if isinstance(variables[0], str):
        slogan = variables[0]
    else:
        slogan = variables[0].get('question_name', 'something')
    name = "%s survey" % slogan
    description = "A survey that asks about %s." % slogan

    spec = []
    index = 0
    for var in vars_list:
        spec_item = {}
        spec_item['index'] = index
        index += 1
        spec_item['required'] = required
        spec_item['choices'] = ''
        spec_item['type'] = default_type
        if isinstance(var, dict):
            spec_item.update(var)
            var_name = spec_item.get('variable', 'variable')
        else:
            var_name = var
        spec_item.setdefault('variable', var_name)
        spec_item.setdefault('question_name', "Enter a value for %s." % var_name)
        spec_item.setdefault('question_description', "A question about %s." % var_name)
        if spec_item['type'] == 'integer':
            spec_item.setdefault('default', 0)
            spec_item.setdefault('max', max or spec_item['default'] + 100)
            spec_item.setdefault('min', min or spec_item['default'] - 100)
        else:
            spec_item.setdefault('default', '')
            if min:
                spec_item.setdefault('min', min)
            if max:
                spec_item.setdefault('max', max)
        spec.append(spec_item)

    survey_spec = {}
    survey_spec['spec'] = spec
    survey_spec['name'] = name
    survey_spec['description'] = description
    return survey_spec


# create methods are intended to be called directly as needed
# or encapsulated by specific factory fixtures in a conftest
#


def create_job_template(name, roles=None, persisted=True, webhook_service='', **kwargs):
    Objects = generate_objects(["job_template", "jobs",
                                "organization",
                                "inventory",
                                "project",
                                "credential", "cloud_credential", "network_credential",
                                "job_type",
                                "survey",], kwargs)

    org = None
    proj = None
    inv = None
    cred = None
    cloud_cred = None
    net_cred = None
    spec = None
    jobs = {}
    job_type = kwargs.get('job_type', 'run')
    extra_vars = kwargs.get('extra_vars', '')

    if 'organization' in kwargs:
        org = kwargs['organization']
        if type(org) is not Organization:
            org = mk_organization(org, org, persisted=persisted)

    if 'credential' in kwargs:
        cred = kwargs['credential']
        if type(cred) is not Credential:
            cred = mk_credential(cred, persisted=persisted)

    if 'cloud_credential' in kwargs:
        cloud_cred = kwargs['cloud_credential']
        if type(cloud_cred) is not Credential:
            cloud_cred = mk_credential(cloud_cred, credential_type='aws', persisted=persisted)

    if 'network_credential' in kwargs:
        net_cred = kwargs['network_credential']
        if type(net_cred) is not Credential:
            net_cred = mk_credential(net_cred, credential_type='net', persisted=persisted)

    if 'project' in kwargs:
        proj = kwargs['project']
        if type(proj) is not Project:
            proj = mk_project(proj, organization=org, persisted=persisted)

    if 'inventory' in kwargs:
        inv = kwargs['inventory']
        if type(inv) is not Inventory:
            inv = mk_inventory(inv, organization=org, persisted=persisted)

    if 'survey' in kwargs:
        spec = create_survey_spec(kwargs['survey'])
    else:
        spec = None

    jt = mk_job_template(name, project=proj, inventory=inv, credential=cred,
                         network_credential=net_cred, cloud_credential=cloud_cred,
                         job_type=job_type, spec=spec, extra_vars=extra_vars,
                         persisted=persisted, webhook_service=webhook_service)

    if 'jobs' in kwargs:
        for i in kwargs['jobs']:
            if type(i) is Job:
                jobs[i.pk] = i
            else:
                # Fill in default survey answers
                job_extra_vars = {}
                if spec is not None:
                    for question in spec['spec']:
                        job_extra_vars[question['variable']] = question['default']
                jobs[i] = mk_job(job_template=jt, project=proj, inventory=inv, credential=cred,
                                 extra_vars=job_extra_vars,
                                 job_type=job_type, persisted=persisted)

    role_objects = generate_role_objects([org, proj, inv, cred])
    apply_roles(roles, role_objects, persisted)

    return Objects(job_template=jt,
                   jobs=jobs,
                   project=proj,
                   inventory=inv,
                   credential=cred, cloud_credential=cloud_cred, network_credential=net_cred,
                   job_type=job_type,
                   organization=org,
                   survey=spec,)


def create_organization(name, roles=None, persisted=True, **kwargs):
    Objects = generate_objects(["organization",
                                "teams", "users",
                                "superusers",
                                "projects",
                                "labels",
                                "notification_templates",
                                "inventories",], kwargs)

    projects = {}
    inventories = {}
    labels = {}
    notification_templates = {}

    org = mk_organization(name, name, persisted=persisted)

    if 'inventories' in kwargs:
        for i in kwargs['inventories']:
            if type(i) is Inventory:
                inventories[i.name] = i
            else:
                inventories[i] = mk_inventory(i, organization=org, persisted=persisted)

    if 'projects' in kwargs:
        for p in kwargs['projects']:
            if type(p) is Project:
                projects[p.name] = p
            else:
                projects[p] = mk_project(p, organization=org, persisted=persisted)

    teams = generate_teams(org, persisted, teams=kwargs.get('teams'))
    superusers = generate_users(org, teams, True, persisted, superusers=kwargs.get('superusers'))
    users = generate_users(org, teams, False, persisted, users=kwargs.get('users'))

    if 'labels' in kwargs:
        for label_obj in kwargs['labels']:
            if type(label_obj) is Label:
                labels[label_obj.name] = label_obj
            else:
                labels[label_obj] = mk_label(label_obj, organization=org, persisted=persisted)

    if 'notification_templates' in kwargs:
        for nt in kwargs['notification_templates']:
            if type(nt) is NotificationTemplate:
                notification_templates[nt.name] = nt
            else:
                notification_templates[nt] = mk_notification_template(nt, organization=org, persisted=persisted)

    role_objects = generate_role_objects([org, superusers, users, teams, projects, labels, notification_templates])
    apply_roles(roles, role_objects, persisted)
    return Objects(organization=org,
                   superusers=_Mapped(superusers),
                   users=_Mapped(users),
                   teams=_Mapped(teams),
                   projects=_Mapped(projects),
                   labels=_Mapped(labels),
                   notification_templates=_Mapped(notification_templates),
                   inventories=_Mapped(inventories))


def create_notification_template(name, roles=None, persisted=True, **kwargs):
    Objects = generate_objects(["notification_template",
                                "organization",
                                "users",
                                "superusers",
                                "teams",], kwargs)

    organization = None

    if 'organization' in kwargs:
        org = kwargs['organization']
        organization = mk_organization(org, '{}-desc'.format(org), persisted=persisted)

    notification_template = mk_notification_template(name, organization=organization, persisted=persisted)

    teams = generate_teams(organization, persisted, teams=kwargs.get('teams'))
    superusers = generate_users(organization, teams, True, persisted, superusers=kwargs.get('superusers'))
    users = generate_users(organization, teams, False, persisted, users=kwargs.get('users'))

    role_objects = generate_role_objects([organization, notification_template])
    apply_roles(roles, role_objects, persisted)
    return Objects(notification_template=notification_template,
                   organization=organization,
                   users=_Mapped(users),
                   superusers=_Mapped(superusers),
                   teams=teams)


def generate_workflow_job_template_nodes(workflow_job_template,
                                         persisted,
                                         **kwargs):

    workflow_job_template_nodes = kwargs.get('workflow_job_template_nodes', [])
    if len(workflow_job_template_nodes) > 0 and not persisted:
        raise RuntimeError('workflow job template nodes cannot be used when persisted=False')

    new_nodes = []

    for i, node in enumerate(workflow_job_template_nodes):
        new_node = WorkflowJobTemplateNode(workflow_job_template=workflow_job_template,
                                           unified_job_template=node['unified_job_template'],
                                           id=i)
        if persisted:
            new_node.save()
        new_nodes.append(new_node)

    node_types = ['success_nodes', 'failure_nodes', 'always_nodes']
    for node_type in node_types:
        for i, new_node in enumerate(new_nodes):
            if node_type not in workflow_job_template_nodes[i]:
                continue
            for related_index in workflow_job_template_nodes[i][node_type]:
                getattr(new_node, node_type).add(new_nodes[related_index])


# TODO: Implement survey and jobs
def create_workflow_job_template(name, organization=None, persisted=True, webhook_service='', **kwargs):
    Objects = generate_objects(["workflow_job_template",
                                "workflow_job_template_nodes",
                                "survey",], kwargs)

    spec = None
    #jobs = None

    extra_vars = kwargs.get('extra_vars', '')

    if 'survey' in kwargs:
        spec = create_survey_spec(kwargs['survey'])

    wfjt = mk_workflow_job_template(name,
                                    organization=organization,
                                    spec=spec,
                                    extra_vars=extra_vars,
                                    persisted=persisted,
                                    webhook_service=webhook_service)



    workflow_jt_nodes = generate_workflow_job_template_nodes(wfjt,
                                                             persisted,
                                                             workflow_job_template_nodes=kwargs.get('workflow_job_template_nodes', []))

    '''
    if 'jobs' in kwargs:
        for i in kwargs['jobs']:
            if type(i) is Job:
                jobs[i.pk] = i
            else:
                # TODO: Create the job
                raise RuntimeError("Currently, only already created jobs are supported")
    '''
    return Objects(workflow_job_template=wfjt,
                   #jobs=jobs,
                   workflow_job_template_nodes=workflow_jt_nodes,
                   survey=spec,)
