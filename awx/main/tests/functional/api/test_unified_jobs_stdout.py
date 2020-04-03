# -*- coding: utf-8 -*-

import base64
import json
import re

from django.conf import settings
from django.utils.encoding import smart_str
from unittest import mock
import pytest

from awx.api.versioning import reverse
from awx.main.models import (Job, JobEvent, AdHocCommand, AdHocCommandEvent,
                             Project, ProjectUpdate, ProjectUpdateEvent,
                             InventoryUpdate, InventorySource,
                             InventoryUpdateEvent, SystemJob, SystemJobEvent)


def _mk_project_update():
    project = Project()
    project.save()
    return ProjectUpdate(project=project)


def _mk_inventory_update():
    source = InventorySource(source='ec2')
    source.save()
    iu = InventoryUpdate(inventory_source=source, source='e2')
    return iu


@pytest.mark.django_db
@pytest.mark.parametrize('Parent, Child, relation, view', [
    [Job, JobEvent, 'job', 'api:job_stdout'],
    [AdHocCommand, AdHocCommandEvent, 'ad_hoc_command', 'api:ad_hoc_command_stdout'],
    [_mk_project_update, ProjectUpdateEvent, 'project_update', 'api:project_update_stdout'],
    [_mk_inventory_update, InventoryUpdateEvent, 'inventory_update', 'api:inventory_update_stdout'],
])
def test_text_stdout(sqlite_copy_expert, Parent, Child, relation, view, get, admin):
    job = Parent()
    job.save()
    for i in range(3):
        Child(**{relation: job, 'stdout': 'Testing {}\n'.format(i), 'start_line': i}).save()
    url = reverse(view, kwargs={'pk': job.pk}) + '?format=txt'

    response = get(url, user=admin, expect=200)
    assert smart_str(response.content).splitlines() == ['Testing %d' % i for i in range(3)]


@pytest.mark.django_db
@pytest.mark.parametrize('Parent, Child, relation, view', [
    [Job, JobEvent, 'job', 'api:job_stdout'],
    [AdHocCommand, AdHocCommandEvent, 'ad_hoc_command', 'api:ad_hoc_command_stdout'],
    [_mk_project_update, ProjectUpdateEvent, 'project_update', 'api:project_update_stdout'],
    [_mk_inventory_update, InventoryUpdateEvent, 'inventory_update', 'api:inventory_update_stdout'],
])
@pytest.mark.parametrize('download', [True, False])
def test_ansi_stdout_filtering(sqlite_copy_expert, Parent, Child, relation,
                               view, download, get, admin):
    job = Parent()
    job.save()
    for i in range(3):
        Child(**{
            relation: job,
            'stdout': '\x1B[0;36mTesting {}\x1B[0m\n'.format(i),
            'start_line': i
        }).save()
    url = reverse(view, kwargs={'pk': job.pk})

    # ansi codes in ?format=txt should get filtered
    fmt = "?format={}".format("txt_download" if download else "txt")
    response = get(url + fmt, user=admin, expect=200)
    assert smart_str(response.content).splitlines() == ['Testing %d' % i for i in range(3)]
    has_download_header = response.has_header('Content-Disposition')
    assert has_download_header if download else not has_download_header

    # ask for ansi and you'll get it
    fmt = "?format={}".format("ansi_download" if download else "ansi")
    response = get(url + fmt, user=admin, expect=200)
    assert smart_str(response.content).splitlines() == ['\x1B[0;36mTesting %d\x1B[0m' % i for i in range(3)]
    has_download_header = response.has_header('Content-Disposition')
    assert has_download_header if download else not has_download_header


@pytest.mark.django_db
@pytest.mark.parametrize('Parent, Child, relation, view', [
    [Job, JobEvent, 'job', 'api:job_stdout'],
    [AdHocCommand, AdHocCommandEvent, 'ad_hoc_command', 'api:ad_hoc_command_stdout'],
    [_mk_project_update, ProjectUpdateEvent, 'project_update', 'api:project_update_stdout'],
    [_mk_inventory_update, InventoryUpdateEvent, 'inventory_update', 'api:inventory_update_stdout'],
])
def test_colorized_html_stdout(sqlite_copy_expert, Parent, Child, relation, view, get, admin):
    job = Parent()
    job.save()
    for i in range(3):
        Child(**{
            relation: job,
            'stdout': '\x1B[0;36mTesting {}\x1B[0m\n'.format(i),
            'start_line': i
        }).save()
    url = reverse(view, kwargs={'pk': job.pk}) + '?format=html'

    response = get(url, user=admin, expect=200)
    assert '.ansi36 { color: #2dbaba; }' in smart_str(response.content)
    for i in range(3):
        assert '<span class="ansi36">Testing {}</span>'.format(i) in smart_str(response.content)


@pytest.mark.django_db
@pytest.mark.parametrize('Parent, Child, relation, view', [
    [Job, JobEvent, 'job', 'api:job_stdout'],
    [AdHocCommand, AdHocCommandEvent, 'ad_hoc_command', 'api:ad_hoc_command_stdout'],
    [_mk_project_update, ProjectUpdateEvent, 'project_update', 'api:project_update_stdout'],
    [_mk_inventory_update, InventoryUpdateEvent, 'inventory_update', 'api:inventory_update_stdout'],
])
def test_stdout_line_range(sqlite_copy_expert, Parent, Child, relation, view, get, admin):
    job = Parent()
    job.save()
    for i in range(20):
        Child(**{relation: job, 'stdout': 'Testing {}\n'.format(i), 'start_line': i}).save()
    url = reverse(view, kwargs={'pk': job.pk}) + '?format=html&start_line=5&end_line=10'

    response = get(url, user=admin, expect=200)
    assert re.findall('Testing [0-9]+', smart_str(response.content)) == ['Testing %d' % i for i in range(5, 10)]


@pytest.mark.django_db
def test_text_stdout_from_system_job_events(sqlite_copy_expert, get, admin):
    job = SystemJob()
    job.save()
    for i in range(3):
        SystemJobEvent(system_job=job, stdout='Testing {}\n'.format(i), start_line=i).save()
    url = reverse('api:system_job_detail', kwargs={'pk': job.pk})
    response = get(url, user=admin, expect=200)
    assert smart_str(response.data['result_stdout']).splitlines() == ['Testing %d' % i for i in range(3)]


@pytest.mark.django_db
def test_text_stdout_with_max_stdout(sqlite_copy_expert, get, admin):
    job = SystemJob()
    job.save()
    total_bytes = settings.STDOUT_MAX_BYTES_DISPLAY + 1
    large_stdout = 'X' * total_bytes
    SystemJobEvent(system_job=job, stdout=large_stdout, start_line=0).save()
    url = reverse('api:system_job_detail', kwargs={'pk': job.pk})
    response = get(url, user=admin, expect=200)
    assert response.data['result_stdout'] == (
        'Standard Output too large to display ({actual} bytes), only download '
        'supported for sizes over {max} bytes.'.format(
            actual=total_bytes,
            max=settings.STDOUT_MAX_BYTES_DISPLAY
        )
    )


@pytest.mark.django_db
@pytest.mark.parametrize('Parent, Child, relation, view', [
    [Job, JobEvent, 'job', 'api:job_stdout'],
    [AdHocCommand, AdHocCommandEvent, 'ad_hoc_command', 'api:ad_hoc_command_stdout'],
    [_mk_project_update, ProjectUpdateEvent, 'project_update', 'api:project_update_stdout'],
    [_mk_inventory_update, InventoryUpdateEvent, 'inventory_update', 'api:inventory_update_stdout'],
])
@pytest.mark.parametrize('fmt', ['txt', 'ansi'])
@mock.patch('awx.main.redact.UriCleaner.SENSITIVE_URI_PATTERN', mock.Mock(**{'search.return_value': None}))  # really slow for large strings
def test_max_bytes_display(sqlite_copy_expert, Parent, Child, relation, view, fmt, get, admin):
    job = Parent()
    job.save()
    total_bytes = settings.STDOUT_MAX_BYTES_DISPLAY + 1
    large_stdout = 'X' * total_bytes
    Child(**{relation: job, 'stdout': large_stdout, 'start_line': 0}).save()
    url = reverse(view, kwargs={'pk': job.pk})

    response = get(url + '?format={}'.format(fmt), user=admin, expect=200)
    assert smart_str(response.content) == (
        'Standard Output too large to display ({actual} bytes), only download '
        'supported for sizes over {max} bytes.'.format(
            actual=total_bytes,
            max=settings.STDOUT_MAX_BYTES_DISPLAY
        )
    )

    response = get(url + '?format={}_download'.format(fmt), user=admin, expect=200)
    assert smart_str(response.content) == large_stdout


@pytest.mark.django_db
@pytest.mark.parametrize('Cls, view', [
    [_mk_project_update, 'api:project_update_stdout'],
    [_mk_inventory_update, 'api:inventory_update_stdout']
])
@pytest.mark.parametrize('fmt', ['txt', 'ansi', 'txt_download', 'ansi_download'])
def test_legacy_result_stdout_text_fallback(Cls, view, fmt, get, admin):
    # older versions of stored raw stdout in a raw text blob at
    # main_unifiedjob.result_stdout_text; this test ensures that fallback
    # works properly if no job events exist
    job = Cls()
    job.save()
    job.result_stdout_text = 'LEGACY STDOUT!'
    job.save()
    url = reverse(view, kwargs={'pk': job.pk})

    response = get(url + '?format={}'.format(fmt), user=admin, expect=200)
    assert smart_str(response.content) == 'LEGACY STDOUT!'


@pytest.mark.django_db
@pytest.mark.parametrize('Cls, view', [
    [_mk_project_update, 'api:project_update_stdout'],
    [_mk_inventory_update, 'api:inventory_update_stdout']
])
@pytest.mark.parametrize('fmt', ['txt', 'ansi'])
@mock.patch('awx.main.redact.UriCleaner.SENSITIVE_URI_PATTERN', mock.Mock(**{'search.return_value': None}))  # really slow for large strings
def test_legacy_result_stdout_with_max_bytes(Cls, view, fmt, get, admin):
    job = Cls()
    job.save()
    total_bytes = settings.STDOUT_MAX_BYTES_DISPLAY + 1
    large_stdout = 'X' * total_bytes
    job.result_stdout_text = large_stdout
    job.save()
    url = reverse(view, kwargs={'pk': job.pk})

    response = get(url + '?format={}'.format(fmt), user=admin, expect=200)
    assert smart_str(response.content) == (
        'Standard Output too large to display ({actual} bytes), only download '
        'supported for sizes over {max} bytes.'.format(
            actual=total_bytes,
            max=settings.STDOUT_MAX_BYTES_DISPLAY
        )
    )

    response = get(url + '?format={}'.format(fmt + '_download'), user=admin, expect=200)
    assert smart_str(response.content) == large_stdout


@pytest.mark.django_db
@pytest.mark.parametrize('Parent, Child, relation, view', [
    [Job, JobEvent, 'job', 'api:job_stdout'],
    [AdHocCommand, AdHocCommandEvent, 'ad_hoc_command', 'api:ad_hoc_command_stdout'],
    [_mk_project_update, ProjectUpdateEvent, 'project_update', 'api:project_update_stdout'],
    [_mk_inventory_update, InventoryUpdateEvent, 'inventory_update', 'api:inventory_update_stdout'],
])
@pytest.mark.parametrize('fmt', ['txt', 'ansi', 'txt_download', 'ansi_download'])
def test_text_with_unicode_stdout(sqlite_copy_expert, Parent, Child, relation,
                                  view, get, admin, fmt):
    job = Parent()
    job.save()
    for i in range(3):
        Child(**{relation: job, 'stdout': u'オ{}\n'.format(i), 'start_line': i}).save()
    url = reverse(view, kwargs={'pk': job.pk}) + '?format=' + fmt

    response = get(url, user=admin, expect=200)
    assert smart_str(response.content).splitlines() == ['オ%d' % i for i in range(3)]


@pytest.mark.django_db
def test_unicode_with_base64_ansi(sqlite_copy_expert, get, admin):
    job = Job()
    job.save()
    for i in range(3):
        JobEvent(job=job, stdout='オ{}\n'.format(i), start_line=i).save()
    url = reverse(
        'api:job_stdout',
        kwargs={'pk': job.pk}
    ) + '?format=json&content_encoding=base64'

    response = get(url, user=admin, expect=200)
    content = base64.b64decode(json.loads(smart_str(response.content))['content'])
    assert smart_str(content).splitlines() == ['オ%d' % i for i in range(3)]
