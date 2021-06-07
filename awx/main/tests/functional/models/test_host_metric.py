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
