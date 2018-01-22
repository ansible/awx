from rest_framework import routers
from awx.network_ui import v1_api_views


router = routers.DefaultRouter()

{%for model in models%}
router.register(r'{{model.name.lower()}}', v1_api_views.{{model.name}}ViewSet){%endfor%}
