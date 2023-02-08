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
    HostMetric.objects.bulk_create([HostMetric(hostname=h, last_automation=current_time) for h in hostnames])

    hm = HostMetric.objects.get(hostname="Host to delete 0")
    assert hm.last_deleted is None

    # soft delete 1st
    hm.soft_delete()
    assert hm.deleted is True
    assert hm.deleted_counter == 1
    assert hm.last_deleted is not None
    last_deleted = hm.last_deleted

    # 2nd delete doesn't have an effect
    hm.soft_delete()
    assert hm.deleted is True
    assert hm.deleted_counter == 1
    assert hm.last_deleted == last_deleted

    # 2nd record is not touched
    hm = HostMetric.objects.get(hostname="Host to delete 1")
    assert hm.deleted is False
    assert hm.deleted_counter == 0
    assert hm.last_deleted is None


@pytest.mark.django_db
def test_soft_restore():
    hostnames = [f'Host to delete {i}' for i in range(2)]
    current_time = now()
    HostMetric.objects.bulk_create([HostMetric(hostname=h, last_automation=current_time) for h in hostnames])
