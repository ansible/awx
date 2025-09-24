import pytest

from awx.main.tests.live.tests.conftest import wait_for_events

from awx.main.models import Job, Inventory


def assert_facts_populated(name):
    job = Job.objects.filter(name__icontains=name).order_by('-created').first()
    assert job is not None
    wait_for_events(job)

    inventory = job.inventory
    assert inventory.hosts.count() > 0  # sanity
    for host in inventory.hosts.all():
        assert host.ansible_facts


@pytest.fixture
def general_facts_test(live_tmp_folder, run_job_from_playbook):
    def _rf(slug, jt_params):
        jt_params['use_fact_cache'] = True
        standard_kwargs = dict(scm_url=f'file://{live_tmp_folder}/facts', jt_params=jt_params)

        # GATHER FACTS
        name = f'test_gather_ansible_facts_{slug}'
        run_job_from_playbook(name, 'gather.yml', **standard_kwargs)
        assert_facts_populated(name)

        # KEEP FACTS
        name = f'test_clear_ansible_facts_{slug}'
        run_job_from_playbook(name, 'no_op.yml', **standard_kwargs)
        assert_facts_populated(name)

        # CLEAR FACTS
        name = f'test_clear_ansible_facts_{slug}'
        run_job_from_playbook(name, 'clear.yml', **standard_kwargs)
        job = Job.objects.filter(name__icontains=name).order_by('-created').first()

        assert job is not None
        wait_for_events(job)
        inventory = job.inventory
        assert inventory.hosts.count() > 0  # sanity
        for host in inventory.hosts.all():
            assert not host.ansible_facts

    return _rf


def test_basic_ansible_facts(general_facts_test):
    general_facts_test('basic', {})


@pytest.fixture
def sliced_inventory():
    inv, _ = Inventory.objects.get_or_create(name='inventory-to-slice')
    if not inv.hosts.exists():
        for i in range(10):
            inv.hosts.create(name=f'sliced_host_{i}')
    return inv


def test_slicing_with_facts(general_facts_test, sliced_inventory):
    general_facts_test('sliced', {'job_slice_count': 3, 'inventory': sliced_inventory.id})
