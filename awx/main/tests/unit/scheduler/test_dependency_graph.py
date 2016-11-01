
# Python
import pytest
from datetime import timedelta

# Django
from django.utils.timezone import now as tz_now

# AWX
from awx.main.scheduler.dependency_graph import DependencyGraph
from awx.main.scheduler.partial import ProjectUpdateDict

@pytest.fixture
def graph():
    return DependencyGraph()

@pytest.fixture
def job():
    return dict(project_id=1)

@pytest.fixture
def unsuccessful_last_project(graph, job):
    pu = ProjectUpdateDict(dict(id=1, 
                                project__scm_update_cache_timeout=999999, 
                                project_id=1, 
                                status='failed', 
                                created='3', 
                                finished='3',))

    graph.add_latest_project_update(pu)

    return graph

@pytest.fixture
def last_dependent_project(graph):
    now = tz_now()

    job = {
        'project_id': 1,
        'created': now,
    }
    pu = ProjectUpdateDict(dict(id=1, project_id=1, status='waiting', 
                                project__scm_update_cache_timeout=0, 
                                launch_type='dependency', 
                                created=now - timedelta(seconds=1),))
    
    graph.add_latest_project_update(pu)

    return (graph, job)

@pytest.fixture
def timedout_project_update(graph, job):
    now = tz_now()

    job = {
        'project_id': 1,
        'created': now,
    }
    pu = ProjectUpdateDict(dict(id=1, project_id=1, status='successful', 
                                project__scm_update_cache_timeout=10, 
                                launch_type='dependency', 
                                created=now - timedelta(seconds=100), 
                                finished=now - timedelta(seconds=11),))
    
    graph.add_latest_project_update(pu)

    return (graph, job)

@pytest.fixture
def not_timedout_project_update(graph, job):
    now = tz_now()

    job = {
        'project_id': 1,
        'created': now,
    }
    pu = ProjectUpdateDict(dict(id=1, project_id=1, status='successful', 
                                project__scm_update_cache_timeout=3600, 
                                launch_type='dependency', 
                                created=now - timedelta(seconds=100), 
                                finished=now - timedelta(seconds=11),))
    
    graph.add_latest_project_update(pu)

    return (graph, job)


class TestShouldUpdateRelatedProject():

    def test_no_project_updates(self, graph, job):
        actual = graph.should_update_related_project(job)

        assert True is actual

    def test_timedout_project_update(self, timedout_project_update):
        (graph, job) = timedout_project_update

        actual = graph.should_update_related_project(job)

        assert True is actual

    def test_not_timedout_project_update(self, not_timedout_project_update):
        (graph, job) = not_timedout_project_update

        actual = graph.should_update_related_project(job)

        assert False is actual

    def test_unsuccessful_last_project(self, unsuccessful_last_project, job):
        graph = unsuccessful_last_project 

        actual = graph.should_update_related_project(job)

        assert True is actual

    def test_last_dependent_project(self, last_dependent_project):
        (graph, job) = last_dependent_project
        
        actual = graph.should_update_related_project(job)
        assert False is actual
        
