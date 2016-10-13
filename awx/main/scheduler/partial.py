
# AWX
from awx.main.models import (
    Job,
    ProjectUpdate,
    InventoryUpdate,
)

class PartialModelDict(object):
    FIELDS = ()
    model = None
    data = None

    def __init__(self, data):
        if type(data) is not dict:
            raise RuntimeError("Expected data to be of type dict not %s" % type(data))
        self.data = data

    def __getitem__(self, index):
        return self.data[index]

    def __setitem__(self, key, value):
        self.data[key] = value

    def get(self, key, **kwargs):
        return self.data.get(key, **kwargs)

    def get_full(self):
        return self.model.objects.get(id=self.data['id'])

    def refresh_partial(self):
        return self.__class__(self.model.objects.filter(id=self.data['id']).values(*self.__class__.get_db_values())[0])

    @classmethod
    def get_partial(cls, id):
        return cls(cls.model.objects.filter(id=id).values(*cls.get_db_values())[0])

    @classmethod
    def get_db_values(cls):
        return cls.FIELDS

    @classmethod
    def filter_partial(cls, status=[]):
        kv = {
            'status__in': status
        }
        return [cls(o) for o in cls.model.objects.filter(**kv).values(*cls.get_db_values())]

    def get_job_type_str(self):
        raise RuntimeError("Inherit and implement me")
    
    def task_impact(self):
        raise RuntimeError("Inherit and implement me")

class JobDict(PartialModelDict):
    FIELDS = (
        'id', 'status', 'job_template_id', 'inventory_id', 'project_id', 
        'launch_type', 'limit', 'allow_simultaneous', 'created', 
        'job_type', 'celery_task_id', 'project__scm_update_on_launch',
        'forks',
    )
    model = Job

    def get_job_type_str(self):
        return 'job'

    def task_impact(self):
        return (5 if self.data['forks'] == 0 else self.data['forks']) * 10

class ProjectUpdateDict(PartialModelDict):
    FIELDS = (
        'id', 'status', 'project_id', 'created', 'celery_task_id', 'launch_type', 'project__scm_update_cache_timeout', 'project__scm_update_on_launch',
    )
    model = ProjectUpdate
    
    def get_job_type_str(self):
        return 'project_update'
    
    def task_impact(self):
        return 10

class ProjectUpdateLatestDict(ProjectUpdateDict):
    FIELDS = (
        'id', 'status', 'project_id', 'created', 'finished', 'project__scm_update_cache_timeout', 'launch_type', 'project__scm_update_on_launch',
    )
    model = ProjectUpdate

    @classmethod
    def filter_partial(cls, project_ids):
        # TODO: This can shurley be made more efficient
        results = []
        for project_id in project_ids:
            qs = cls.model.objects.filter(project_id=project_id, status__in=['waiting', 'successful', 'failed']).order_by('-finished')
            if qs.count() > 0:
                results.append(cls(cls.model.objects.filter(id=qs[0].id).values(*cls.get_db_values())[0]))
        return results

class InventoryUpdateDict(PartialModelDict):
    FIELDS = (
        'id', 'status', 'created', 'celery_task_id',
    )
    model = InventoryUpdate

    def get_job_type_str(self):
        return 'inventory_update'

    def task_impact(self):
        return 20

