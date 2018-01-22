

.PHONY: all models admin v1_api_serializers v1_api_views v1_api_urls v2_api_serializers v2_api_views v2_api_urls

all: models admin v1_api_serializers v1_api_views v1_api_urls v2_api_serializers v2_api_views v2_api_urls 

models:
	jinja2 templates/models.pyt designs/models.yml > models.py
	autopep8 -i models.py --ignore-local-config --max-line-length 160

admin:
	jinja2 templates/admin.pyt designs/models.yml > admin.py
	autopep8 -i admin.py --ignore-local-config --max-line-length 160

v1_api_serializers:
	jinja2 templates/v1_api_serializers.pyt designs/models.yml > v1_api_serializers.py
	autopep8 -i v1_api_serializers.py --ignore-local-config --max-line-length 160

v1_api_views:
	jinja2 templates/v1_api_views.pyt designs/models.yml > v1_api_views.py
	autopep8 -i v1_api_views.py --ignore-local-config --max-line-length 160

v1_api_urls:
	jinja2 templates/v1_api_urls.pyt designs/models.yml > v1_api_urls.py
	autopep8 -i v1_api_urls.py --ignore-local-config --max-line-length 160

v2_api_serializers:
	jinja2 templates/v2_api_serializers.pyt designs/models.yml > v2_api_serializers.py
	autopep8 -i v2_api_serializers.py --ignore-local-config --max-line-length 160

v2_api_views:
	jinja2 templates/v2_api_views.pyt designs/models.yml > v2_api_views.py
	autopep8 -i v2_api_views.py --ignore-local-config --max-line-length 160

v2_api_urls:
	jinja2 templates/v2_api_urls.pyt designs/models.yml > v2_api_urls.py
	autopep8 -i v2_api_urls.py --ignore-local-config --max-line-length 160
