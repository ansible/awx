# -*- coding: utf-8 -*-
# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

# Python
import pytest

# AWX
from awx.api.versioning import reverse
from awx.conf.registry import settings_registry

TEST_GIF_LOGO = 'data:image/gif;base64,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'  # NOQA
TEST_PNG_LOGO = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACEAAAAjCAYAAAAaLGNkAAAAAXNSR0IB2cksfwAAAdVpVFh0WE1MOmNvbS5hZG9iZS54bXAAAAAAADx4OnhtcG1ldGEgeG1sbnM6eD0iYWRvYmU6bnM6bWV0YS8iIHg6eG1wdGs9IlhNUCBDb3JlIDUuNC4wIj4KICAgPHJkZjpSREYgeG1sbnM6cmRmPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1zeW50YXgtbnMjIj4KICAgICAgPHJkZjpEZXNjcmlwdGlvbiByZGY6YWJvdXQ9IiIKICAgICAgICAgICAgeG1sbnM6dGlmZj0iaHR0cDovL25zLmFkb2JlLmNvbS90aWZmLzEuMC8iPgogICAgICAgICA8dGlmZjpDb21wcmVzc2lvbj4xPC90aWZmOkNvbXByZXNzaW9uPgogICAgICAgICA8dGlmZjpQaG90b21ldHJpY0ludGVycHJldGF0aW9uPjI8L3RpZmY6UGhvdG9tZXRyaWNJbnRlcnByZXRhdGlvbj4KICAgICAgICAgPHRpZmY6T3JpZW50YXRpb24+MTwvdGlmZjpPcmllbnRhdGlvbj4KICAgICAgPC9yZGY6RGVzY3JpcHRpb24+CiAgIDwvcmRmOlJERj4KPC94OnhtcG1ldGE+Cjl0tmoAAAHVSURBVFgJ7VZRsoMgDNTOu5E9U+/Ud6Z6JssGNg2oNKD90xkHCNnNkgTbYbieKwNXBn6bgSXQ4+16xi5UDiqDN3Pecr6+1fM5DHh7n1NEIPjjoRLKzOjG3qQ5dRtEy2LCjh/Gz2wDZE2nZYKkrxdn/kY9XQQkGCGqqDY5IgJFkEKgBCzDNGXhTKEye7boFRH6IPJj5EshiNCSjV4R4eSx7zhmR2tcdIuwmWiMeao7e0JHViZEWUI5aP8a9O+rx74D6sGEiJftiX3YeueIiFXg2KrhpqzjVC3dPZFYJZ7NOwwtNwM8R0UkLfH0sT5qck+OlkMq0BucKr0iWG7gpAQksD9esM1z3Lnf6SHjLh67nnKEGxC/iomWhByTeXOQJGHHcKxwHhHKnt1HIdYtmexkIb/HOURWTSJqn2gKMDG0bDUc/D0iAseovxUBoylmQCug6IVhSv+4DIeKI94jAr4AjiSEgQ25JYB+YWT9BZ94AM8erwgFkRifaArA6U0G5KT0m//z26REZuK9okgrT6VwE1jTHjbVzyNAyRwTEPOtuiex9FVBNZCkruaA4PZqFp1u8Rpww9/6rcK5y0EkAxRiZJt79PWOVYWGRE9pbJhavMengMflGyumk0akMsQnAAAAAElFTkSuQmCC'  # NOQA
TEST_JPEG_LOGO = 'data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAASABIAAD/4QBkRXhpZgAATU0AKgAAAAgAAwEGAAMAAAABAAIAAAESAAMAAAABAAEAAIdpAAQAAAABAAAAMgAAAAAAA6ABAAMAAAABAAEAAKACAAQAAAABAAAAIaADAAQAAAABAAAAIwAAAAD/4QkhaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wLwA8P3hwYWNrZXQgYmVnaW49Iu+7vyIgaWQ9Ilc1TTBNcENlaGlIenJlU3pOVGN6a2M5ZCI/PiA8eDp4bXBtZXRhIHhtbG5zOng9ImFkb2JlOm5zOm1ldGEvIiB4OnhtcHRrPSJYTVAgQ29yZSA1LjQuMCI+IDxyZGY6UkRGIHhtbG5zOnJkZj0iaHR0cDovL3d3dy53My5vcmcvMTk5OS8wMi8yMi1yZGYtc3ludGF4LW5zIyI+IDxyZGY6RGVzY3JpcHRpb24gcmRmOmFib3V0PSIiLz4gPC9yZGY6UkRGPiA8L3g6eG1wbWV0YT4gICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICA8P3hwYWNrZXQgZW5kPSJ3Ij8+AP/tADhQaG90b3Nob3AgMy4wADhCSU0EBAAAAAAAADhCSU0EJQAAAAAAENQdjNmPALIE6YAJmOz4Qn7/wAARCAAjACEDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9sAQwAGBgYGBgYKBgYKDgoKCg4SDg4ODhIXEhISEhIXHBcXFxcXFxwcHBwcHBwcIiIiIiIiJycnJycsLCwsLCwsLCws/9sAQwEHBwcLCgsTCgoTLh8aHy4uLi4uLi4uLi4uLi4uLi4uLi4uLi4uLi4uLi4uLi4uLi4uLi4uLi4uLi4uLi4uLi4u/90ABAAD/9oADAMBAAIRAxEAPwD6poormvFfivSvB2lHVtWLGMtsRE2hnYKzlVLsi52oxALDdjauWKqQCXQfFXh7xP8Aaf7AvYrz7HL5U3lk/K3YjIGVODtcZVsHBODXQV806bcT+E9L03XbCOS2udMsLQanbB4po72xYMfOQpKYyV2zPEwcNwVK7WAr6WriwWMWIUvdcZRdmnuu33rVFSjYKKKK7ST/0PqmuF8Vv4X8S+HNZ0+e/gIsYJvtEsL+bJZsI3UuyxNvBA3gpxvXchyCRXdV8ta3bW667DoloW1y10tLLTJxZWP2hoLSGYzNHclGZpJC0ESk8IAZcRB8is61T2cHK1/1DrY526h8YXHh691vxCz6dafY5Q0U7yGSeQxSxohNzJLcbUeQ4VnVNxBRCWL19b2eraVqE9xa2F3BcS2jbJ0ikV2ibJG1wpJU5UjBx0PpXzrrniy4k17TrrWrGex022ufMijvd9m11PGH8naXKqsUcgR3MhB5U7MA16x4L8F3vhq2sY9Ru4rg6day2tusEAhCrcOkknmEMRI2Y1AcLGT8xYMzZHjZFGu6cquKjaUnt2XS76vv/SN8RVjOdoKyXY9Cooor3TA//9H6pr4gfxRrMvxJ0/whLJE+maVrcVnZRtBCzwQQ3SIipMU80fKignflgPmJr7fr4A/5rf8A9zJ/7eUAdX8SfGviPwl8TtaPh6eK1eTyN0n2eCSUg28OV8ySNn2/KDtztzzjNfZVhY2umWMGm2KeXb2sSQxJknakYCqMkknAHUnNfBXxt/5Kdq//AG7/APpPFX3/AEAFFFFAH//Z'  # NOQA


@pytest.mark.django_db
def test_url_base_defaults_to_request(options, admin):
    # If TOWER_URL_BASE is not set, default to the Tower request hostname
    resp = options(reverse('api:setting_singleton_detail', kwargs={'category_slug': 'system'}), user=admin, expect=200)
    assert resp.data['actions']['PUT']['TOWER_URL_BASE']['default'] == 'http://testserver'


@pytest.mark.django_db
def test_jobs_settings(get, put, patch, delete, admin):
    url = reverse('api:setting_singleton_detail', kwargs={'category_slug': 'jobs'})
    get(url, user=admin, expect=200)
    delete(url, user=admin, expect=204)
    response = get(url, user=admin, expect=200)
    data = dict(response.data.items())
    put(url, user=admin, data=data, expect=200)
    patch(url, user=admin, data={'AWX_ISOLATION_SHOW_PATHS': ['/home']}, expect=200)
    response = get(url, user=admin, expect=200)
    assert response.data['AWX_ISOLATION_SHOW_PATHS'] == ['/home']
    data.pop('AWX_ISOLATION_SHOW_PATHS')
    data.pop('AWX_ANSIBLE_CALLBACK_PLUGINS')
    put(url, user=admin, data=data, expect=200)
    response = get(url, user=admin, expect=200)
    assert response.data['AWX_ISOLATION_SHOW_PATHS'] == []
    assert response.data['AWX_ANSIBLE_CALLBACK_PLUGINS'] == []


@pytest.mark.django_db
@pytest.mark.parametrize(
    'value, expected',
    [
        [True, 400],
        ['invalid', 400],
        [['also', 'invalid'], 400],
        [{}, 200],
        [{'X_FOO': 'VALID'}, 200],
        [{'X_TOTAL': 100}, 200],
        [{'X_FOO': ['ALSO', 'INVALID']}, 400],
        [{'X_FOO': {'ALSO': 'INVALID'}}, 400],
    ],
)
def test_awx_task_env_validity(get, patch, admin, value, expected):
    url = reverse('api:setting_singleton_detail', kwargs={'category_slug': 'jobs'})
    patch(url, user=admin, data={'AWX_TASK_ENV': value}, expect=expected)

    resp = get(url, user=admin)
    if expected == 200:
        assert resp.data['AWX_TASK_ENV'] == dict((k, str(v)) for k, v in value.items())
    else:
        assert resp.data['AWX_TASK_ENV'] == dict()


@pytest.mark.django_db
def test_ui_settings(get, put, patch, delete, admin):
    url = reverse('api:setting_singleton_detail', kwargs={'category_slug': 'ui'})
    response = get(url, user=admin, expect=200)
    assert not response.data['CUSTOM_LOGO']
    assert not response.data['CUSTOM_LOGIN_INFO']
    put(url, user=admin, data=response.data, expect=200)
    patch(url, user=admin, data={'CUSTOM_LOGO': 'data:text/plain;base64,'}, expect=400)
    patch(url, user=admin, data={'CUSTOM_LOGO': 'data:image/png;base64,00'}, expect=400)
    patch(url, user=admin, data={'CUSTOM_LOGO': TEST_GIF_LOGO}, expect=200)
    response = get(url, user=admin, expect=200)
    assert response.data['CUSTOM_LOGO'] == TEST_GIF_LOGO
    patch(url, user=admin, data={'CUSTOM_LOGO': TEST_PNG_LOGO}, expect=200)
    response = get(url, user=admin, expect=200)
    assert response.data['CUSTOM_LOGO'] == TEST_PNG_LOGO
    patch(url, user=admin, data={'CUSTOM_LOGO': TEST_JPEG_LOGO}, expect=200)
    response = get(url, user=admin, expect=200)
    assert response.data['CUSTOM_LOGO'] == TEST_JPEG_LOGO
    patch(url, user=admin, data={'CUSTOM_LOGO': ''}, expect=200)
    response = get(url, user=admin, expect=200)
    assert not response.data['CUSTOM_LOGO']
    patch(url, user=admin, data={'CUSTOM_LOGIN_INFO': 'Customize Me!'}, expect=200)
    response = get(url, user=admin, expect=200)
    assert response.data['CUSTOM_LOGIN_INFO']
    patch(url, user=admin, data={'CUSTOM_LOGIN_INFO': ''}, expect=200)
    response = get(url, user=admin, expect=200)
    assert not response.data['CUSTOM_LOGIN_INFO']
    delete(url, user=admin, expect=204)
    response = get(url, user=admin, expect=200)
    assert not response.data['CUSTOM_LOGO']
    assert not response.data['CUSTOM_LOGIN_INFO']


@pytest.mark.django_db
def test_logging_aggregator_connection_test_requires_superuser(post, alice):
    url = reverse('api:setting_logging_test')
    post(url, {}, user=alice, expect=403)


@pytest.mark.django_db
def test_logging_aggregator_connection_test_not_enabled(post, admin):
    url = reverse('api:setting_logging_test')
    resp = post(url, {}, user=admin, expect=409)
    assert 'Logging not enabled' in resp.data.get('error')


def _mock_logging_defaults():
    # Pre-populate settings obj with defaults
    class MockSettings:
        pass

    mock_settings_obj = MockSettings()
    mock_settings_json = dict()
    for key in settings_registry.get_registered_settings(category_slug='logging'):
        value = settings_registry.get_setting_field(key).get_default()
        setattr(mock_settings_obj, key, value)
        mock_settings_json[key] = value
    setattr(mock_settings_obj, 'MAX_EVENT_RES_DATA', 700000)
    return mock_settings_obj, mock_settings_json


@pytest.mark.parametrize(
    'key, value, error',
    [
        ['LOG_AGGREGATOR_TYPE', 'logstash', 'Cannot enable log aggregator without providing host.'],
        ['LOG_AGGREGATOR_HOST', 'https://logstash', 'Cannot enable log aggregator without providing type.'],
    ],
)
@pytest.mark.django_db
def test_logging_aggregator_missing_settings(put, post, admin, key, value, error):
    _, mock_settings = _mock_logging_defaults()
    mock_settings['LOG_AGGREGATOR_ENABLED'] = True
    mock_settings[key] = value
    url = reverse('api:setting_singleton_detail', kwargs={'category_slug': 'logging'})
    response = put(url, data=mock_settings, user=admin, expect=400)
    assert error in str(response.data)


@pytest.mark.parametrize(
    'type, host, port, username, password',
    [
        ['logstash', 'localhost', 8080, 'logger', 'mcstash'],
        ['loggly', 'http://logs-01.loggly.com/inputs/1fd38090-hash-h4a$h-8d80-t0k3n71/tag/http/', None, None, None],
        ['splunk', 'https://yoursplunk:8088/services/collector/event', None, None, None],
        ['other', '97.221.40.41', 9000, 'logger', 'mcstash'],
        ['sumologic', 'https://endpoint5.collection.us2.sumologic.com/receiver/v1/http/Zagnw_f9XGr_zZgd-_EPM0hb8_rUU7_RU8Q==', None, None, None],
    ],
)
@pytest.mark.django_db
def test_logging_aggregator_valid_settings(put, post, admin, type, host, port, username, password):
    _, mock_settings = _mock_logging_defaults()
    # type = 'splunk'
    # host = 'https://yoursplunk:8088/services/collector/event'
    mock_settings['LOG_AGGREGATOR_ENABLED'] = True
    mock_settings['LOG_AGGREGATOR_TYPE'] = type
    mock_settings['LOG_AGGREGATOR_HOST'] = host
    if port:
        mock_settings['LOG_AGGREGATOR_PORT'] = port
    if username:
        mock_settings['LOG_AGGREGATOR_USERNAME'] = username
    if password:
        mock_settings['LOG_AGGREGATOR_PASSWORD'] = password
    url = reverse('api:setting_singleton_detail', kwargs={'category_slug': 'logging'})
    response = put(url, data=mock_settings, user=admin, expect=200)
    assert type in response.data.get('LOG_AGGREGATOR_TYPE')
    assert host in response.data.get('LOG_AGGREGATOR_HOST')
    if port:
        assert port == response.data.get('LOG_AGGREGATOR_PORT')
    if username:
        assert username in response.data.get('LOG_AGGREGATOR_USERNAME')
    if password:  # Note: password should be encrypted
        assert '$encrypted$' in response.data.get('LOG_AGGREGATOR_PASSWORD')


@pytest.mark.django_db
def test_logging_aggregator_connection_test_valid(put, post, admin):
    _, mock_settings = _mock_logging_defaults()
    type = 'other'
    host = 'https://localhost'
    mock_settings['LOG_AGGREGATOR_ENABLED'] = True
    mock_settings['LOG_AGGREGATOR_TYPE'] = type
    mock_settings['LOG_AGGREGATOR_HOST'] = host
    # POST to save these mock settings
    url = reverse('api:setting_singleton_detail', kwargs={'category_slug': 'logging'})
    put(url, data=mock_settings, user=admin, expect=200)
    # "Test" the logger
    url = reverse('api:setting_logging_test')
    post(url, {}, user=admin, expect=202)
