

.PHONY: all models admin v1_api_serializers v1_api_views v1_api_urls v2_api_serializers v2_api_views v1_api_client v2_api_urls v2_api_access v2_api_client

all: tuples models admin v1_api_serializers v1_api_views v1_api_urls v2_api_serializers v2_api_views v1_api_client action_plugins v2_api_urls v2_api_access v2_api_client

tuples:
	jinja2 templates/tuples.pyt designs/models.yml > tuples.py
	autopep8 -i tuples.py --ignore-local-config --max-line-length 160

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
	autopep8 -i v1_api_views.py --ignore-local-config --max-line-length 80

v1_api_urls:
	jinja2 templates/v1_api_urls.pyt designs/models.yml > v1_api_urls.py
	autopep8 -i v1_api_urls.py --ignore-local-config --max-line-length 160

v2_api_urls:
	jinja2 templates/v2_api_urls.pyt designs/models.yml > v2_api_urls.py
	autopep8 -i v2_api_urls.py --ignore-local-config --max-line-length 160

v2_api_access:
	jinja2 templates/v2_api_access.pyt designs/models.yml > v2_api_access.py
	autopep8 -i v2_api_access.py --ignore-local-config --max-line-length 160

v2_api_serializers:
	jinja2 templates/v2_api_serializers.pyt designs/models.yml > v2_api_serializers.py
	autopep8 -i v2_api_serializers.py --ignore-local-config --max-line-length 160

v2_api_views:
	jinja2 templates/v2_api_views.pyt designs/models.yml > v2_api_views.py
	autopep8 -i v2_api_views.py --ignore-local-config --max-line-length 160

v1_api_client:
	jinja2 templates/v1_api_client.pyt designs/models.yml > client/v1_api_client.py
	autopep8 -i client/v1_api_client.py --ignore-local-config --max-line-length 160

v2_api_client:
	jinja2 templates/v2_api_client.pyt designs/models.yml > client/v2_api_client.py
	autopep8 -i client/v2_api_client.py --ignore-local-config --max-line-length 160

action_plugins: ap_create_model ap_get_model ap_delete_model ap_update_model ap_list_model

ap_create_model:
	jinja2 templates/action_plugins/create_model.pyt designs/models.yml > action_plugins/create_model.py
	cd action_plugins; csplit -k -f create_ create_model.py '/#----/' '{*}'
	rm action_plugins/create_model.py
	./tools/fix_action_plugin_names.py action_plugins/create_*
	autopep8 -i action_plugins/create_*.py --ignore-local-config --max-line-length 160
	jinja2 templates/library/create_model.pyt designs/models.yml > library/create_model.py
	cd library; csplit -k -f create_ create_model.py '/#----/' '{*}'
	rm library/create_model.py
	./tools/fix_action_plugin_names.py library/create_*
	autopep8 -i library/create_*.py --ignore-local-config --max-line-length 160


ap_update_model:
	jinja2 templates/action_plugins/update_model.pyt designs/models.yml > action_plugins/update_model.py
	cd action_plugins; csplit -k -f update_ update_model.py '/#----/' '{*}'
	rm action_plugins/update_model.py
	./tools/fix_action_plugin_names.py action_plugins/update_*
	autopep8 -i action_plugins/update_*.py --ignore-local-config --max-line-length 160
	jinja2 templates/library/update_model.pyt designs/models.yml > library/update_model.py
	cd library; csplit -k -f update_ update_model.py '/#----/' '{*}'
	rm library/update_model.py
	./tools/fix_action_plugin_names.py library/update_*
	autopep8 -i library/update_*.py --ignore-local-config --max-line-length 160


ap_get_model:
	jinja2 templates/action_plugins/get_model.pyt designs/models.yml > action_plugins/get_model.py
	cd action_plugins; csplit -k -f get_ get_model.py '/#----/' '{*}'
	rm action_plugins/get_model.py
	./tools/fix_action_plugin_names.py action_plugins/get_*
	autopep8 -i action_plugins/get_*.py --ignore-local-config --max-line-length 160
	jinja2 templates/library/get_model.pyt designs/models.yml > library/get_model.py
	cd library; csplit -k -f get_ get_model.py '/#----/' '{*}'
	rm library/get_model.py
	./tools/fix_action_plugin_names.py library/get_*
	autopep8 -i library/get_*.py --ignore-local-config --max-line-length 160


ap_delete_model:
	jinja2 templates/action_plugins/delete_model.pyt designs/models.yml > action_plugins/delete_model.py
	cd action_plugins; csplit -k -f delete_ delete_model.py '/#----/' '{*}'
	rm action_plugins/delete_model.py
	./tools/fix_action_plugin_names.py action_plugins/delete_*
	autopep8 -i action_plugins/delete_*.py --ignore-local-config --max-line-length 160
	jinja2 templates/library/delete_model.pyt designs/models.yml > library/delete_model.py
	cd library; csplit -k -f delete_ delete_model.py '/#----/' '{*}'
	rm library/delete_model.py
	./tools/fix_action_plugin_names.py library/delete_*
	autopep8 -i library/delete_*.py --ignore-local-config --max-line-length 160


ap_list_model:
	jinja2 templates/action_plugins/list_model.pyt designs/models.yml > action_plugins/list_model.py
	cd action_plugins; csplit -k -f list_ list_model.py '/#----/' '{*}'
	rm action_plugins/list_model.py
	./tools/fix_action_plugin_names.py action_plugins/list_*
	autopep8 -i action_plugins/list_*.py --ignore-local-config --max-line-length 160
	jinja2 templates/library/list_model.pyt designs/models.yml > library/list_model.py
	cd library; csplit -k -f list_ list_model.py '/#----/' '{*}'
	rm library/list_model.py
	./tools/fix_action_plugin_names.py library/list_*
	autopep8 -i library/list_*.py --ignore-local-config --max-line-length 160

