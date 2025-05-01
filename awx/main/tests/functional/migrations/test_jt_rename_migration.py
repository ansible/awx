import pytest

from awx.main.migrations._db_constraints import _rename_duplicates
from awx.main.models import JobTemplate


@pytest.mark.django_db
def test_rename_job_template_duplicates(organization, project):
    ids = []
    for i in range(5):
        jt = JobTemplate.objects.create(name=f'jt-{i}', organization=organization, project=project)
        ids.append(jt.id)  # saved in order of creation

    # Hack to first allow duplicate names of JT to test migration
    JobTemplate.objects.filter(id__in=ids).update(org_unique=False)

    # Set all JTs to the same name
    JobTemplate.objects.filter(id__in=ids).update(name='same_name_for_test')

    _rename_duplicates(JobTemplate)

    first_jt = JobTemplate.objects.get(id=ids[0])
    assert first_jt.name == 'same_name_for_test'

    for i, pk in enumerate(ids):
        if i == 0:
            continue
        jt = JobTemplate.objects.get(id=pk)
        # Name should be set based on creation order
        assert jt.name == f'same_name_for_test_dup{i}'


@pytest.mark.django_db
def test_rename_job_template_name_too_long(organization, project):
    ids = []
    for i in range(3):
        jt = JobTemplate.objects.create(name=f'jt-{i}', organization=organization, project=project)
        ids.append(jt.id)  # saved in order of creation

    JobTemplate.objects.filter(id__in=ids).update(org_unique=False)

    chars = 512
    # Set all JTs to the same reaaaaaaly long name
    JobTemplate.objects.filter(id__in=ids).update(name='A' * chars)

    _rename_duplicates(JobTemplate)

    first_jt = JobTemplate.objects.get(id=ids[0])
    assert first_jt.name == 'A' * chars

    for i, pk in enumerate(ids):
        if i == 0:
            continue
        jt = JobTemplate.objects.get(id=pk)
        assert jt.name.endswith(f'dup{i}')
        assert len(jt.name) <= 512
