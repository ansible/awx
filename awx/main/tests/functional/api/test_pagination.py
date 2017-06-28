import pytest

from awx.main.models.inventory import Group, Host
from awx.api.pagination import Pagination


@pytest.fixture
def host(inventory):
    def handler(name, groups):
        h = Host(name=name, inventory=inventory)
        h.save()
        h = Host.objects.get(name=name, inventory=inventory)
        for g in groups:
            h.groups.add(g)
        h.save()
        h = Host.objects.get(name=name, inventory=inventory)
        return h
    return handler


@pytest.fixture
def group(inventory):
    def handler(name):
        g = Group(name=name, inventory=inventory)
        g.save()
        g = Group.objects.get(name=name, inventory=inventory)
        return g
    return handler


@pytest.mark.django_db
def test_pagination_backend_output_correct_total_count(group, host):
    # NOTE: this test might not be db-backend-agnostic. Manual tests might be needed also
    g1 = group('pg_group1')
    g2 = group('pg_group2')
    host('pg_host1', [g1, g2])
    queryset = Host.objects.filter(groups__name__in=('pg_group1', 'pg_group2')).distinct()
    p = Pagination().django_paginator_class(queryset, 10)
    p.page(1)
    assert p.count == 1
