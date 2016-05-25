from django.contrib.auth.models import User

from awx.main.models import (
    Organization,
    Project,
    Team,
    Instance,
    JobTemplate,
    NotificationTemplate,
    Credential,
    Inventory,
    Label,
)

# mk methods should create only a single object of a single type.
# they should also have the option of being persisted or not.
# if the object must be persisted an error should be raised when
# persisted=False
#

def mk_instance(persisted=True):
    if not persisted:
        raise RuntimeError('creating an Instance requires persisted=True')
    from django.conf import settings
    return Instance.objects.get_or_create(uuid=settings.SYSTEM_UUID, primary=True, hostname="instance.example.org")


def mk_organization(name, desc, persisted=True):
    org = Organization(name=name, description=desc)
    if persisted:
        mk_instance(True)
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
        mk_instance(True)
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


def mk_notification_template(name, **kwargs):
    nt = NotificationTemplate(name=name)
    nt.notification_type = kwargs.get('type', 'webhook')

    configuration = kwargs.get('configuration',
                               dict(url="http://localhost", headers={"Test": "Header"}))
    nt.notification_configuration = configuration

    organization = kwargs.get('organization')
    if organization is not None:
        nt.organization = organization
    if kwargs.get('persisted', True):
        nt.save()
    return nt


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

