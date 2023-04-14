from awxkit.api.resources import resources
from . import base
from . import page


class HostMetric(base.Base):
    def get(self, **query_parameters):
        request = self.connection.get(self.endpoint, query_parameters, headers={'Accept': 'application/json'})
        return self.page_identity(request)


class HostMetrics(page.PageList, HostMetric):
    pass


page.register_page([resources.host_metric], HostMetric)

page.register_page([resources.host_metrics], HostMetrics)
