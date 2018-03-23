import pytest

# AWX
from awx.main.models import JobTemplate, JobLaunchConfig


@pytest.fixture
def full_jt(inventory, project, machine_credential):
    jt = JobTemplate.objects.create(
        name='my-jt',
        inventory=inventory,
        project=project,
        playbook='helloworld.yml'
    )
    jt.credentials.add(machine_credential)
    return jt


@pytest.fixture
def config_factory(full_jt):
    def return_config(data):
        job = full_jt.create_unified_job(**data)
        try:
            return job.launch_config
        except JobLaunchConfig.DoesNotExist:
            return None
    return return_config


@pytest.mark.django_db
class TestConfigCreation:
    '''
    Checks cases for the auto-creation of a job configuration with the
    creation of a unified job
    '''
    def test_null_configuration(self, full_jt):
        job = full_jt.create_unified_job()
        assert job.launch_config.prompts_dict() == {}

    def test_char_field_change(self, full_jt):
        job = full_jt.create_unified_job(limit='foobar')
        config = job.launch_config
        assert config.limit == 'foobar'
        assert config.char_prompts == {'limit': 'foobar'}

    def test_added_credential(self, full_jt, credential):
        job = full_jt.create_unified_job(credentials=[credential])
        config = job.launch_config
        assert set(config.credentials.all()) == set([credential])

    def test_survey_passwords_ignored(self, inventory_source):
        iu = inventory_source.create_unified_job(
            survey_passwords={'foo': '$encrypted$'}
        )
        assert iu.launch_config.prompts_dict() == {}


@pytest.mark.django_db
class TestConfigReversibility:
    '''
    Checks that a blob of saved prompts will be re-created in the
    prompts_dict for launching new jobs
    '''
    def test_char_field_only(self, config_factory):
        config = config_factory({'limit': 'foobar'})
        assert config.prompts_dict() == {'limit': 'foobar'}

    def test_related_objects(self, config_factory, inventory, credential):
        prompts = {
            'limit': 'foobar',
            'inventory': inventory,
            'credentials': set([credential])
        }
        config = config_factory(prompts)
        assert config.prompts_dict() == prompts
