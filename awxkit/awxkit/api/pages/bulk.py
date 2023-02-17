from awxkit.api.resources import resources
from . import base
from . import page


class Bulk(base.Base):
    def get(self, **query_parameters):
        request = self.connection.get(self.endpoint, query_parameters, headers={'Accept': 'application/json'})
        return self.page_identity(request)


page.register_page([resources.bulk, (resources.bulk, 'get')], Bulk)


class BulkJobLaunch(base.Base):
    def post(self, payload={}):
        result = self.connection.post(self.endpoint, payload)
        if 'url' in result.json():
            return self.walk(result.json()['url'])
        else:
            return self.page_identity(result, request_json={})


page.register_page(resources.bulk_job_launch, BulkJobLaunch)
