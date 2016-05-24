from collections import namedtuple

from django.contrib.auth.models import User
from django.conf import settings

from awx.main.models import (
    Organization,
    Project,
    Team,
    Instance,
    JobTemplate,
    Credential,
    Inventory,
    Label,
    Role,
)


def instance():
    return Instance.objects.get_or_create(uuid=settings.SYSTEM_UUID, primary=True, hostname="instance.example.org")


def mk_organization(name, desc, persisted=True):
    org = Organization(name=name, description=desc)
    if persisted:
        instance()
        org.save()
    return org


def mk_label(name, **kwargs):
    label = Label(name=name, description="%s-desc".format(name))
    organization = kwargs.get('organization')
    if organization is not None:
        label.organization = organization
    if kwargs.get('persisted', True):
        label.save()
    return label


def mk_team(name, **kwargs):
    team = Team(name=name)
    organization = kwargs.get('organization')
    if organization is not None:
        team.organization = organization
    if kwargs.get('persisted', True):
        instance()
        team.save()
    return team


def mk_user(name, **kwargs):
    user = User(username=name, is_superuser=kwargs.get('is_superuser', False))

    if kwargs.get('persisted', True):
        user.save()
        organization = kwargs.get('organization')
        if organization is not None:
            organization.member_role.members.add(user)
        team = kwargs.get('team')
        if team is not None:
            team.member_role.members.add(user)
    return user


def mk_project(name, **kwargs):
    project = Project(name=name)
    organization = kwargs.get('organization')
    if organization is not None:
        project.organization = organization
    if kwargs.get('persisted', True):
        project.save()
    return project


def mk_credential(name, **kwargs):
    cred = Credential(name=name)
    cred.cloud = kwargs.get('cloud', False)
    cred.kind = kwargs.get('kind', 'ssh')
    if kwargs.get('persisted', True):
        cred.save()
    return cred


def mk_inventory(name, **kwargs):
    inv = Inventory(name=name)
    organization = kwargs.get('organization', None)
    if organization is not None:
        inv.organization = organization
    if kwargs.get('persisted', True):
        inv.save()
    return inv

def mk_job_template(name, **kwargs):
    jt = JobTemplate(name=name, job_type=kwargs.get('job_type', 'run'))

    jt.inventory = kwargs.get('inventory', None)
    if jt.inventory is None:
        jt.ask_inventory_on_launch = True

    jt.credential = kwargs.get('credential', None)
    if jt.credential is None:
        jt.ask_credential_on_launch = True

    jt.project = kwargs.get('project', None)

    if kwargs.get('persisted', True):
        jt.save()
    return jt


class _Mapped(object):
    def __init__(self, d):
        self.d = d
        for k,v in d.items():
            setattr(self, k.replace(' ','_'), v)

    def all(self):
        return self.d.values()

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

    return Objects(job_template=jt,
                   project=proj,
                   inventory=inv,
                   credential=cred,
                   job_type=job_type)

def create_organization(name, **kwargs):
    Objects = namedtuple("Objects", "organization,teams,users,superusers,projects,labels,roles")

    org = mk_organization(name, '%s-desc'.format(name))

    superusers = {}
    users = {}
    teams = {}
    projects = {}
    labels = {}
    roles = {}
    persisted = kwargs.get('persisted', True)

    if 'teams' in kwargs:
        for t in kwargs['teams']:
            if type(t) is Team:
                teams[t.name] = t
            else:
                teams[t] = mk_team(t, organization=org, persisted=persisted)

    if 'projects' in kwargs:
        for p in kwargs['projects']:
            if type(p) is Project:
                projects[p.name] = p
            else:
                projects[p] = mk_project(p, organization=org, persisted=persisted)

    if 'superusers' in kwargs:
        # remove this duplication eventually
        for u in kwargs['superusers']:
            if type(u) is User:
                users[u.username] = u
            else:
                p1, sep, p2 = u.partition(':')
                if p2:
                    t = teams[p1]
                    superusers[p2] = mk_user(p2, organization=org, team=t, is_superuser=True, persisted=persisted)
                else:
                    superusers[p1] = mk_user(p1, organization=org, team=None, is_superuser=True, persisted=persisted)

    if 'users' in kwargs:
        # remove this duplication eventually
        for u in kwargs['users']:
            if type(u) is User:
                users[u.username] = u
            else:
                p1, sep, p2 = u.partition(':')
                if p2:
                    t = teams[p1]
                    users[p2] = mk_user(p2, organization=org, team=t, is_superuser=False, persisted=persisted)
                else:
                    users[p1] = mk_user(p1, organization=org, is_superuser=False, persisted=persisted)

    if 'labels' in kwargs:
        for l in kwargs['labels']:
            if type(l) is Label:
                labels[l.name] = l
            else:
                labels[l] = mk_label(l, org, persisted=persisted)

    if 'roles' in kwargs:
        # refactor this .. alot
        if not persisted:
            raise RuntimeError('roles can not be used when persisted=False')

        all_objects = {}
        for d in [superusers, users, teams, projects, labels]:
            for k,v in d.iteritems():
                if all_objects.get(k) is not None:
                    raise KeyError('object names must be unique when using roles \
                                   {} key already exists with value {}'.format(k,v))
                all_objects[k] = v

        for role in kwargs.get('roles'):
            obj_role, sep, member_role = role.partition(':')
            if not member_role:
                raise RuntimeError('you must an assignment role, got None')

            obj_str, o_role_str = obj_role.split('.')
            member_str, m_sep, m_role_str = member_role.partition('.')

            obj = all_objects[obj_str]
            obj_role = getattr(obj, o_role_str)

            member = all_objects[member_str]
            if m_role_str:
                if hasattr(member, m_role_str):
                    member_role = getattr(member, m_role_str)
                    obj_role.parents.add(member_role)
                else:
                    raise RuntimeError('unable to find {} role for {}'.format(m_role_str, member_str))
            else:
                if type(member) is User:
                    obj_role.members.add(member)
                else:
                    raise RuntimeError('unable to add non-user {} for members list of {}'.format(member_str, obj_str))

    return Objects(organization=org,
                   superusers=_Mapped(superusers),
                   users=_Mapped(users),
                   teams=_Mapped(teams),
                   projects=_Mapped(projects),
                   labels=_Mapped(labels),
                   roles=_Mapped(roles))
