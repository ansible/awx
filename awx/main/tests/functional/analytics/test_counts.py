import pytest

from awx.main import models
from awx.main.analytics import collectors


@pytest.mark.django_db
def test_empty():
    assert collectors.counts(None) == {
        "active_user_sessions": 0,
        "active_anonymous_sessions": 0,
        "active_sessions": 0,
        "active_host_count": 0,
        "credential": 0,
        "custom_inventory_script": 0,
        "custom_virtualenvs": 0,  # dev env ansible3
        "host": 0,
        "inventory": 0,
        "inventories": {"normal": 0, "smart": 0},
        "job_template": 0,
        "notification_template": 0,
        "organization": 0,
        "project": 0,
        "running_jobs": 0,
        "schedule": 0,
        "team": 0,
        "user": 0,
        "workflow_job_template": 0,
        "unified_job": 0,
        "pending_jobs": 0,
    }


@pytest.mark.django_db
def test_database_counts(
    organization_factory, job_template_factory, workflow_job_template_factory
):
    objs = organization_factory("org", superusers=["admin"])
    jt = job_template_factory(
        "test",
        organization=objs.organization,
        inventory="test_inv",
        project="test_project",
        credential="test_cred",
    )
    workflow_job_template_factory("test")
    models.Team(organization=objs.organization).save()
    models.Host(inventory=jt.inventory).save()
    models.Schedule(
        rrule="DTSTART;TZID=America/New_York:20300504T150000",
        unified_job_template=jt.job_template,
    ).save()
    models.CustomInventoryScript(organization=objs.organization).save()

    counts = collectors.counts(None)
    for key in (
        "organization",
        "team",
        "user",
        "inventory",
        "credential",
        "project",
        "job_template",
        "workflow_job_template",
        "host",
        "schedule",
        "custom_inventory_script",
    ):
        assert counts[key] == 1


@pytest.mark.django_db
def test_inventory_counts(organization_factory, inventory_factory):
    (inv1, inv2, inv3) = [inventory_factory(f"inv-{i}") for i in range(3)]

    s1 = inv1.inventory_sources.create(name="src1", source="ec2")
    s2 = inv1.inventory_sources.create(name="src2", source="file")
    s3 = inv1.inventory_sources.create(name="src3", source="gce")

    s1.hosts.create(name="host1", inventory=inv1)
    s1.hosts.create(name="host2", inventory=inv1)
    s1.hosts.create(name="host3", inventory=inv1)

    s2.hosts.create(name="host4", inventory=inv1)
    s2.hosts.create(name="host5", inventory=inv1)

    s3.hosts.create(name="host6", inventory=inv1)

    s1 = inv2.inventory_sources.create(name="src1", source="ec2")

    s1.hosts.create(name="host1", inventory=inv2)
    s1.hosts.create(name="host2", inventory=inv2)
    s1.hosts.create(name="host3", inventory=inv2)

    inv_counts = collectors.inventory_counts(None)

    assert {
        inv1.id: {
            "name": "inv-0",
            "kind": "",
            "hosts": 6,
            "sources": 3,
            "source_list": [
                {"name": "src1", "source": "ec2", "num_hosts": 3},
                {"name": "src2", "source": "file", "num_hosts": 2},
                {"name": "src3", "source": "gce", "num_hosts": 1},
            ],
        },
        inv2.id: {
            "name": "inv-1",
            "kind": "",
            "hosts": 3,
            "sources": 1,
            "source_list": [{"name": "src1", "source": "ec2", "num_hosts": 3}],
        },
        inv3.id: {
            "name": "inv-2",
            "kind": "",
            "hosts": 0,
            "sources": 0,
            "source_list": [],
        },
    } == inv_counts
