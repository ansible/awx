import pytest
from django.utils.timezone import now
from awx.main.models import HostMetric


@pytest.mark.django_db
def test_host_metrics_generation():
    hostnames = [f'Host {i}' for i in range(100)]
    current_time = now()
    HostMetric.objects.bulk_create([HostMetric(hostname=h, last_automation=current_time) for h in hostnames])

    # 3 assertions have to be made
    # 1) if all the objects were created or not
    assert HostMetric.objects.count() == len(hostnames)

    # 2) Match the hostnames stored in DB with the one passed in bulk_create
    assert sorted([s.hostname for s in HostMetric.objects.all()]) == sorted(hostnames)

    # 3) Make sure that first_automation attribute is today's date
    date_today = now().strftime('%Y-%m-%d')
    result = HostMetric.objects.filter(first_automation__startswith=date_today).count()
    assert result == len(hostnames)


@pytest.mark.django_db
def test_soft_delete():
    hostnames = [f'Host to delete {i}' for i in range(2)]
    current_time = now()
    HostMetric.objects.bulk_create([HostMetric(hostname=h, last_automation=current_time, automated_counter=42) for h in hostnames])

    hm = HostMetric.objects.get(hostname="Host to delete 0")
    assert hm.last_deleted is None

    last_deleted = None
    for _ in range(3):
        # soft delete 1st
        # 2nd/3rd delete don't have an effect
        hm.soft_delete()
        if last_deleted is None:
            last_deleted = hm.last_deleted

        assert hm.deleted is True
        assert hm.deleted_counter == 1
        assert hm.last_deleted == last_deleted
        assert hm.automated_counter == 42

    # 2nd record is not touched
    hm = HostMetric.objects.get(hostname="Host to delete 1")
    assert hm.deleted is False
    assert hm.deleted_counter == 0
    assert hm.last_deleted is None
    assert hm.automated_counter == 42


@pytest.mark.django_db
def test_soft_restore():
    current_time = now()
    HostMetric.objects.create(hostname="Host 1", last_automation=current_time, deleted=True)
    HostMetric.objects.create(hostname="Host 2", last_automation=current_time, deleted=True, last_deleted=current_time)
    HostMetric.objects.create(hostname="Host 3", last_automation=current_time, deleted=False, last_deleted=current_time)
    HostMetric.objects.all().update(automated_counter=42, deleted_counter=10)

    # 1. deleted, last_deleted not null
    for hm in HostMetric.objects.all():
        for _ in range(3):
            hm.soft_restore()
            assert hm.deleted is False
            assert hm.automated_counter == 42 and hm.deleted_counter == 10
            if hm.hostname == "Host 1":
                assert hm.last_deleted is None
            else:
                assert hm.last_deleted == current_time
