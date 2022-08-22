import json
import insights_analytics_collector as base
from django.core.serializers.json import DjangoJSONEncoder


class CollectionJSON(base.CollectionJSON):
    def _save_gathering(self, data):
        self.data = json.dumps(data, cls=DjangoJSONEncoder)
