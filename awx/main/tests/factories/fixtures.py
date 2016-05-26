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


def mk_organization(name, description=None, persisted=True):
    description = description or '{}-description'.format(name)
    org = Organization(name=name, description=description)
    if persisted:
        mk_instance(persisted)
        org.save()
    return org


def mk_label(name, organization=None, description=None, persisted=True):
    description = description or '{}-description'.format(name)
    label = Label(name=name, description=description)
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
        mk_instance(persisted)
        team.save()
    return team


def mk_user(name, is_superuser=False, organization=None, team=None, persisted=True):
    user = User(username=name, is_superuser=is_superuser)
    if persisted:
        user.save()
        if organization is not None:
            organization.member_role.members.add(user)
        if team is not None:
            team.member_role.members.add(user)
    return user


def mk_project(name, organization=None, description=None, persisted=True):
    description = description or '{}-description'.format(name)
    project = Project(name=name, description=description)
    if organization is not None:
        project.organization = organization
    if persisted:
        project.save()
    return project


def mk_credential(name, cloud=False, kind='ssh', persisted=True):
    cred = Credential(name=name, cloud=cloud, kind=kind)
    if persisted:
        cred.save()
    return cred


def mk_notification_template(name, notification_type='webhook', configuration=None, organization=None, persisted=True):
    nt = NotificationTemplate(name=name)
    nt.notification_type = notification_type
    nt.notification_configuration = configuration or dict(url="http://localhost", headers={"Test": "Header"})

    if organization is not None:
        nt.organization = organization
    if persisted:
        nt.save()
    return nt


def mk_inventory(name, organization=None, persisted=True):
    inv = Inventory(name=name)
    if organization is not None:
        inv.organization = organization
    if persisted:
        inv.save()
    return inv


def mk_job_template(name, job_type='run',
                    organization=None, inventory=None,
                    credential=None, persisted=True,
                    project=None):
    jt = JobTemplate(name=name, job_type=job_type, playbook='mocked')

    jt.inventory = inventory
    if jt.inventory is None:
        jt.ask_inventory_on_launch = True

    jt.credential = credential
    if jt.credential is None:
        jt.ask_credential_on_launch = True

    jt.project = project

    if persisted:
        jt.save()
    return jt
