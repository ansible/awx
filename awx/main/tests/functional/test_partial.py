
# Python
import pytest
from django.utils.timezone import now as tz_now
from datetime import timedelta

# AWX
from awx.main.models import (
    Project,
    ProjectUpdate,
)
from awx.main.scheduler.partial import (
    ProjectUpdateLatestDict,
)


@pytest.fixture
def failed_project_update():
    p = Project.objects.create(name="proj1")
    pu = ProjectUpdate.objects.create(project=p, status='failed', finished=tz_now() - timedelta(seconds=20))

    return (p, pu)

@pytest.fixture
def successful_project_update():
    p = Project.objects.create(name="proj1")
    pu = ProjectUpdate.objects.create(project=p, status='successful', finished=tz_now() - timedelta(seconds=20))

    return (p, pu)

# Failed project updates newer than successful ones
@pytest.fixture
def multiple_project_updates():
    p = Project.objects.create(name="proj1")

    epoch = tz_now()

    successful_pus = [ProjectUpdate.objects.create(project=p,
                                                   status='successful', 
                                                   finished=epoch - timedelta(seconds=100 + i)) for i in xrange(0, 5)]
    failed_pus = [ProjectUpdate.objects.create(project=p, 
                                               status='failed',
                                               finished=epoch - timedelta(seconds=100 - len(successful_pus) + i)) for i in xrange(0, 5)]
    return (p, failed_pus, successful_pus)

class TestProjectUpdateLatestDictDict():
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


