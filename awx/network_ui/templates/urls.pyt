from rest_framework import routers
from awx.network_ui import api_views


router = routers.DefaultRouter()

{%for model in models%}
router.register(r'{{model.name.lower()}}', api_views.{{model.name}}ViewSet){%endfor%}
