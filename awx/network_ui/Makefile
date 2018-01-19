

.PHONY: all models admin api_serializers api_views api_urls

all: models admin api_serializers api_views api_urls

models:
	jinja2 templates/models.pyt designs/models.yml > models.py
	autopep8 -i models.py --ignore-local-config --max-line-length 160

admin:
	jinja2 templates/admin.pyt designs/models.yml > admin.py
	autopep8 -i admin.py --ignore-local-config --max-line-length 160

api_serializers:
	jinja2 templates/serializers.pyt designs/models.yml > api_serializers.py
	autopep8 -i api_serializers.py --ignore-local-config --max-line-length 160

api_views:
	jinja2 templates/views.pyt designs/models.yml > api_views.py
	autopep8 -i api_views.py --ignore-local-config --max-line-length 160

api_urls:
	jinja2 templates/urls.pyt designs/models.yml > api_urls.py
	autopep8 -i api_urls.py --ignore-local-config --max-line-length 160
