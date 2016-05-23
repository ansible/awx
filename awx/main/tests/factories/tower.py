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
)

def instance():
    return Instance.objects.get_or_create(uuid=settings.SYSTEM_UUID, primary=True, hostname="instance.example.org")

def mk_organization(name, desc, persisted=True):
    org = Organization(name=name, description=desc)
    if persisted:
        instance()
        org.save()
    return org

def mk_label(name, organization=None, persisted=True):
    label = Label(name=name, description="%s-desc".format(name))
    if organization is not None:
        label.organization = organization
    if persisted:
        label.save()
    return label

def mk_team(name, organization=None, persisted=True):
    team = Team(name=name)
    if organization is not None:
        team.organization = organization
    if persisted:
        instance()
        team.save()
    return team


def mk_user(name, organization=None, team=None, is_superuser=False, persisted=True):
    user = User(username=name)

    if persisted:
        user.save()
        if organization is not None:
            organization.member_role.members.add(user)
        if team is not None:
            team.member_role.members.add(user)
    return user


def mk_project(name, organization=None, persisted=True):
    project = Project(name=name)

    if organization is not None:
        project.organization = organization
    if persisted:
        project.save()
    return project


def mk_credential(name, *args, **kwargs):
    return None

def mk_inventory(name, organization=None, persisted=True):
    inv = Inventory(name=name)
    inv.organization = organization
    if persisted:
        inv.save()
    return inv

def mk_job_template(name, project=None, inventory=None, credential=None, job_type='run', persisted=True):
    jt = JobTemplate(name=name, job_type=job_type)
    jt.project = project
    jt.inventory = inventory
    jt.credential = credential
    if persisted:
        jt.save()
    return jt


class _Mapped(object):
    def __init__(self, d):
        self.d = d
        for k,v in d.items():
            setattr(self, k, v)

    def all(self):
        return self.d.values()

def create_job_template(name, *args, **kwargs):
    Objects = namedtuple("Objects", "organization, job_template, inventory, project, credential")

    org = None
    proj = None
    inv = None
    cred = None

    if 'organization' in kwargs:
        org = kwargs['organization']
        if type(org) is not Organization:
            org = mk_organization(org, '%s-desc'.format(org))

    if 'credential' in kwargs:
        cred = kwargs['credential']
        if type(cred) is not Credential:
            cred = mk_credential(cred)

    if 'project' in kwargs:
        proj = kwargs['project']
        if type(proj) is not Project:
            proj = mk_project(proj, org)

    if 'inventory' in kwargs:
        inv = kwargs['inventory']
        if type(inv) is not Inventory:
            inv = mk_inventory(inv, org)

    jt = mk_job_template(name, proj, inv, cred)

    return Objects(job_template=jt,
                   project=proj,
                   inventory=inv,
                   credential=cred)

def create_organization(name, *args, **kwargs):
    Objects = namedtuple("Objects", "organization,teams,users,superusers,projects,labels")

    org = mk_organization(name, '%s-desc'.format(name))

    superusers = {}
    users = {}
    teams = {}
    projects = {}
    labels = {}

    if 'teams' in kwargs:
        for t in kwargs['teams']:
            if type(t) is Team:
                teams[t.name] = t
            else:
                teams[t] = mk_team(t, org)

    if 'projects' in kwargs:
        for p in kwargs['projects']:
            if type(p) is Project:
                projects[p.name] = p
            else:
                projects[p] = mk_project(p, org)

    if 'superusers' in kwargs:
        # remove this duplication eventually
        for u in kwargs['superusers']:
            if type(u) is User:
                users[u.username] = u
            else:
                p1, sep, p2 = u.partition(':')
                if p2:
                    t = teams[p1]
                    superusers[p2] = mk_user(p2, org, t, True)
                else:
                    superusers[p1] = mk_user(p1, org, None, True)

    if 'users' in kwargs:
        # remove this duplication eventually
        for u in kwargs['users']:
            if type(u) is User:
                users[u.username] = u
            else:
                p1, sep, p2 = u.partition(':')
                if p2:
                    t = teams[p1]
                    users[p2] = mk_user(p2, org, t)
                else:
                    users[p1] = mk_user(p1, org)

    if 'labels' in kwargs:
        for l in kwargs['labels']:
            if type(l) is Label:
                labels[l.name] = l
            else:
                labels[l] = mk_label(l, org)

    return Objects(organization=org,
                   superusers=_Mapped(superusers),
                   users=_Mapped(users),
                   teams=_Mapped(teams),
                   projects=_Mapped(projects),
                   labels=_Mapped(labels))


