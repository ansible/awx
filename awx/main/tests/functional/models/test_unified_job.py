import pytest


class TestCreateUnifiedJob:
    '''
    Ensure that copying a job template to a job handles many to many field copy
    '''
    @pytest.mark.django_db
    def test_many_to_many(self, mocker, job_template_labels):
        jt = job_template_labels
        _get_unified_job_field_names = mocker.patch('awx.main.models.jobs.JobTemplate._get_unified_job_field_names', return_value=['labels'])
        j = jt.create_unified_job()

        _get_unified_job_field_names.assert_called_with()
        assert j.labels.all().count() == 2
        assert j.labels.all()[0] == jt.labels.all()[0]
        assert j.labels.all()[1] == jt.labels.all()[1]

    '''
    Ensure that data is looked for in parameter list before looking at the object
    '''
    @pytest.mark.django_db
    def test_many_to_many_kwargs(self, mocker, job_template_labels):
        jt = job_template_labels
        mocked = mocker.MagicMock()
        mocked.__class__.__name__ = 'ManyRelatedManager'
        kwargs = {
            'labels': mocked
        }
        _get_unified_job_field_names = mocker.patch('awx.main.models.jobs.JobTemplate._get_unified_job_field_names', return_value=['labels'])
        jt.create_unified_job(**kwargs)

        _get_unified_job_field_names.assert_called_with()
        mocked.all.assert_called_with()
