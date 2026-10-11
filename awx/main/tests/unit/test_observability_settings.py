from awx.settings.functions import OBSERVABILITY_APP, merge_observability, observability_service_name

APPS = ['django.contrib.auth', 'awx.main', 'ansible_base.rbac']


def _settings(**extra):
    return {'INSTALLED_APPS': list(APPS), **extra}


class TestMergeObservability:
    def test_off_without_an_endpoint(self):
        assert merge_observability(_settings()) == {}
        assert merge_observability(_settings(ANSIBLE_OBSERVABILITY_OTLP_ENDPOINT=None)) == {}
        assert merge_observability(_settings(ANSIBLE_OBSERVABILITY_OTLP_ENDPOINT='')) == {}

    def test_an_endpoint_adds_the_app_and_names_the_process(self):
        data = merge_observability(_settings(ANSIBLE_OBSERVABILITY_OTLP_ENDPOINT='http://collector:4317'), argv=['/usr/bin/uwsgi', '--ini', 'x'])
        assert data == {'INSTALLED_APPS': APPS + [OBSERVABILITY_APP], 'ANSIBLE_OBSERVABILITY_SERVICE_NAME': 'awx-uwsgi'}

    def test_the_app_is_never_added_twice_and_an_explicit_name_is_kept(self):
        settings = _settings(
            ANSIBLE_OBSERVABILITY_OTLP_ENDPOINT='http://collector:4317',
            ANSIBLE_OBSERVABILITY_SERVICE_NAME='controller',
            INSTALLED_APPS=APPS + [OBSERVABILITY_APP],
        )
        assert merge_observability(settings, argv=['uwsgi']) == {}

    def test_the_middleware_is_not_touched(self):
        data = merge_observability(_settings(ANSIBLE_OBSERVABILITY_OTLP_ENDPOINT='http://collector:4317'), argv=['daphne'])
        assert 'MIDDLEWARE' not in data


class TestObservabilityServiceName:
    def test_names_by_process(self):
        assert observability_service_name(['/var/lib/awx/venv/awx/bin/uwsgi', '--ini', 'x']) == 'awx-uwsgi'
        assert observability_service_name(['/var/lib/awx/venv/awx/bin/daphne', '-u', 'x']) == 'awx-daphne'
        assert observability_service_name(['/usr/bin/awx-manage', 'run_dispatcher']) == 'awx-dispatcher'
        assert observability_service_name(['awx-manage', 'run_callback_receiver']) == 'awx-callback-receiver'
        assert observability_service_name(['python3', '-m', 'awx-manage', 'migrate']) == 'awx-migrate'
        assert observability_service_name(['python3', '-c', 'import awx']) == 'awx'
        assert observability_service_name([]) == 'awx'
