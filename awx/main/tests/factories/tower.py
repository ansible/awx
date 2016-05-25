from collections import namedtuple

from django.contrib.auth.models import User

from awx.main.models import (
    Organization,
    Project,
    Team,
    NotificationTemplate,
    Credential,
    Inventory,
    Label,
)

from .fixtures import (
    mk_organization,
    mk_team,
    mk_user,
    mk_job_template,
    mk_credential,
    mk_inventory,
    mk_project,
    mk_label,
    mk_notification_template,
)

from .exc import NotUnique


def build_role_objects(objects):
    '''build_role_objects assembles a dictionary of all possible objects by name.
    It will raise an exception if any of the objects share a name due to the fact that
    it is to be used with apply_roles, which expects unique object names.

    roles share a common name e.g. admin_role, member_role. This ensures that the
    roles short hand used for mapping Roles and Users in apply_roles will function as desired.
    '''
    combined_objects = {}
    for o in objects:
        if type(o) is dict:
            for k,v in o.iteritems():
                if combined_objects.get(k) is not None:
                    raise NotUnique(k, combined_objects)
                combined_objects[k] = v
        elif hasattr(o, 'name'):
            if combined_objects.get(o.name) is not None:
                raise NotUnique(o.name, combined_objects)
            combined_objects[o.name] = o
        else:
            raise RuntimeError('expected a list of dict or list of list, got a type {}'.format(type(o)))
    return combined_objects

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
        raise RuntimeError('roles can not be used when persisted=False')

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


class _Mapped(object):
    '''_Mapped is a helper class that replaces spaces and dashes
    in the name of an object and assigns the object as an attribute

         input: {'my org': Organization}
         output: instance.my_org = Organization
    '''
    def __init__(self, d):
        self.d = d
        for k,v in d.items():
            k = k.replace(' ', '_')
            k = k.replace('-', '_')

            setattr(self, k.replace(' ','_'), v)

    def all(self):
        return self.d.values()

# create methods are intended to be called directly as needed
# or encapsulated by specific factory fixtures in a conftest
#

def create_job_template(name, **kwargs):
    Objects = namedtuple("Objects", "job_template, inventory, project, credential, job_type")

    org = None
    proj = None
    inv = None
    cred = None
    job_type = kwargs.get('job_type', 'run')
    persisted = kwargs.get('persisted', True)

    if 'organization' in kwargs:
        org = kwargs['organization']
        if type(org) is not Organization:
            org = mk_organization(org, '%s-desc'.format(org), persisted=persisted)

    if 'credential' in kwargs:
        cred = kwargs['credential']
        if type(cred) is not Credential:
            cred = mk_credential(cred, persisted=persisted)

    if 'project' in kwargs:
        proj = kwargs['project']
        if type(proj) is not Project:
            proj = mk_project(proj, organization=org, persisted=persisted)

    if 'inventory' in kwargs:
        inv = kwargs['inventory']
        if type(inv) is not Inventory:
            inv = mk_inventory(inv, organization=org, persisted=persisted)

    jt = mk_job_template(name, project=proj,
                         inventory=inv, credential=cred,
                         job_type=job_type, persisted=persisted)

    role_objects = build_role_objects([org, proj, inv, cred])
    apply_roles(kwargs.get('roles'), role_objects, persisted)

    return Objects(job_template=jt,
                   project=proj,
                   inventory=inv,
                   credential=cred,
                   job_type=job_type)

def create_organization(name, **kwargs):
    Objects = namedtuple("Objects", "organization,teams,users,superusers,projects,labels,notification_templates")

    projects = {}
    labels = {}
    notification_templates = {}
    persisted = kwargs.get('persisted', True)

    org = mk_organization(name, '%s-desc'.format(name), persisted=persisted)

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
        for l in kwargs['labels']:
            if type(l) is Label:
                labels[l.name] = l
            else:
                labels[l] = mk_label(l, organization=org, persisted=persisted)

    if 'notification_templates' in kwargs:
        for nt in kwargs['notification_templates']:
            if type(nt) is NotificationTemplate:
                notification_templates[nt.name] = nt
            else:
                notification_templates[nt] = mk_notification_template(nt, organization=org, persisted=persisted)

    role_objects = build_role_objects([superusers, users, teams, projects, labels, notification_templates])
    apply_roles(kwargs.get('roles'), role_objects, persisted)
    return Objects(organization=org,
                   superusers=_Mapped(superusers),
                   users=_Mapped(users),
                   teams=_Mapped(teams),
                   projects=_Mapped(projects),
                   labels=_Mapped(labels),
                   notification_templates=_Mapped(notification_templates))

def create_notification_template(name, **kwargs):
    Objects = namedtuple("Objects", "notification_template,organization,users,superusers,teams")

    organization = None
    persisted = kwargs.get('persisted', True)

    if 'organization' in kwargs:
        org = kwargs['organization']
        organization = mk_organization(org, persisted=persisted)

    notification_template = mk_notification_template(name, organization=organization, persisted=persisted)

    teams = generate_teams(organization, persisted, teams=kwargs.get('teams'))
    superusers = generate_users(org, teams, True, persisted, superusers=kwargs.get('superusers'))
    users = generate_users(org, teams, False, persisted, users=kwargs.get('users'))

    role_objects = build_role_objects([organization, notification_template])
    apply_roles(kwargs.get('roles'), role_objects, persisted)
    return Objects(notification_template=notification_template,
                   organization=organization,
                   users=users,
                   superusers=superusers,
                   teams=teams)
