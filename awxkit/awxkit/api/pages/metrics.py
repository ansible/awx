from prometheus_client.parser import text_string_to_metric_families

from awxkit.api.resources import resources
from . import base
from . import page


class Metrics(base.Base):

    def get(self, **query_parameters):
        request = self.connection.get(self.endpoint, query_parameters)
        self.page_identity(request, ignore_json_errors=True)
        parsed_metrics = text_string_to_metric_families(request.text)
        data = {}
        for family in parsed_metrics:
            for sample in family.samples:
                data[sample[0]] = {"labels": sample[1], "value": sample[2]}
        request.json = lambda: data
        return self.page_identity(request)


page.register_page([resources.metrics,
                    (resources.metrics, 'get')], Metrics)
