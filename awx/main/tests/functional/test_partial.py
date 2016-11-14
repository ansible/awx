
# Python
import pytest
from django.utils.timezone import now as tz_now
from datetime import timedelta

# AWX
from awx.main.models import (
    Organization,
    Inventory,
    Group,
    Project,
    ProjectUpdate,
    InventoryUpdate,
    InventorySource,
)
from awx.main.scheduler.partial import (
    ProjectUpdateLatestDict,
    InventoryUpdateDict,
    InventoryUpdateLatestDict,
)

@pytest.fixture
def org():
    return Organization.objects.create(name="org1")

class TestProjectUpdateLatestDictDict():
    @pytest.fixture
    def successful_project_update(self):
        p = Project.objects.create(name="proj1")
        pu = ProjectUpdate.objects.create(project=p, status='successful', finished=tz_now() - timedelta(seconds=20))

        return (p, pu)
    
    # Failed project updates newer than successful ones
    @pytest.fixture
    def multiple_project_updates(self):
        p = Project.objects.create(name="proj1")

        epoch = tz_now()

        successful_pus = [ProjectUpdate.objects.create(project=p,
                                                       status='successful', 
                                                       finished=epoch - timedelta(seconds=100 + i)) for i in xrange(0, 5)]
        failed_pus = [ProjectUpdate.objects.create(project=p, 
                                                   status='failed',
                                                   finished=epoch - timedelta(seconds=100 - len(successful_pus) + i)) for i in xrange(0, 5)]
        return (p, failed_pus, successful_pus)


    @pytest.mark.django_db
    class TestFilterPartial():
        def test_project_update_successful(self, successful_project_update):
            (project, project_update) = successful_project_update

            tasks = ProjectUpdateLatestDict.filter_partial(project_ids=[project.id])

            assert 1 == len(tasks)
            assert project_update.id == tasks[0]['id']

        def test_correct_project_update(self, multiple_project_updates):
            (project, failed_pus, successful_pus) = multiple_project_updates

            tasks = ProjectUpdateLatestDict.filter_partial(project_ids=[project.id])

            assert 1 == len(tasks)
            assert failed_pus[0].id == tasks[0]['id']


class TestInventoryUpdateDict():
    @pytest.fixture
    def waiting_inventory_update(self, org):
        i = Inventory.objects.create(name='inv1', organization=org)
        g = Group.objects.create(name='group1', inventory=i)
        #Inventory.groups.add(g)
        inv_src = InventorySource.objects.create(group=g)
        iu = InventoryUpdate.objects.create(inventory_source=inv_src, status='waiting')
        return iu

    @pytest.mark.django_db
    class TestFilterPartial():
        def test_simple(self, waiting_inventory_update):
            tasks = InventoryUpdateDict.filter_partial(status=['waiting'])

            assert 1 == len(tasks)
            assert waiting_inventory_update.id == tasks[0]['id']

class TestInventoryUpdateLatestDict():
    @pytest.fixture
    def inventory(self, org):
        i = Inventory.objects.create(name='inv1', organization=org)
        return i

    @pytest.fixture
    def inventory_updates(self, inventory):
        g1 = Group.objects.create(name='group1', inventory=inventory)
        g2 = Group.objects.create(name='group2', inventory=inventory)
        g3 = Group.objects.create(name='group3', inventory=inventory)

        inv_src1 = InventorySource.objects.create(group=g1, update_on_launch=True, inventory=inventory)
        inv_src2 = InventorySource.objects.create(group=g2, update_on_launch=False, inventory=inventory)
        inv_src3 = InventorySource.objects.create(group=g3, update_on_launch=True, inventory=inventory)

        import time
        iu1 = InventoryUpdate.objects.create(inventory_source=inv_src1, status='successful')
        time.sleep(0.1)
        iu2 = InventoryUpdate.objects.create(inventory_source=inv_src2, status='waiting')
        time.sleep(0.1)
        iu3 = InventoryUpdate.objects.create(inventory_source=inv_src3, status='waiting')
        return [iu1, iu2, iu3]

    @pytest.mark.django_db
    def test_filter_partial(self, inventory, inventory_updates):
        
        tasks = InventoryUpdateLatestDict.filter_partial([inventory.id])

        inventory_updates_expected = [inventory_updates[0], inventory_updates[2]]

        assert 2 == len(tasks)
        task_ids = [task['id'] for task in tasks]
        for inventory_update in inventory_updates_expected:
            inventory_update.id in task_ids
    
