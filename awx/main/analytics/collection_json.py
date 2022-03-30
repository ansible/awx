import json
from insights_analytics_collector import CollectionJSON as AnalyticsCollectionJSON
from django.core.serializers.json import DjangoJSONEncoder


class CollectionJSON(AnalyticsCollectionJSON):
    def _save_gathering(self, data):
        self.data = json.dumps(data, cls=DjangoJSONEncoder)
