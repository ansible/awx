import pytest

# AWX
from awx.main.models.jobs import JobTemplate, LaunchTimeConfigBase
from awx.main.models.execution_environments import ExecutionEnvironment


@pytest.fixture
def full_jt(inventory, project, machine_credential):
    jt = JobTemplate.objects.create(name='my-jt', inventory=inventory, project=project, playbook='helloworld.yml')
    jt.credentials.add(machine_credential)
    return jt


@pytest.mark.django_db
class TestConfigCreation:
    """
    Checks cases for the auto-creation of a job configuration with the
    creation of a unified job
    """

    def test_null_configuration(self, full_jt):
        job = full_jt.create_unified_job()
        assert job.launch_config.prompts_dict() == {}

    def test_char_field_change(self, full_jt):
        job = full_jt.create_unified_job(limit='foobar')
        config = job.launch_config
        assert config.limit == 'foobar'
        assert config.char_prompts == {'limit': 'foobar'}

    def test_added_related(self, full_jt, credential, default_instance_group, label):
        job = full_jt.create_unified_job(credentials=[credential], instance_groups=[default_instance_group], labels=[label])
        config = job.launch_config
        assert set(config.credentials.all()) == set([credential])
        assert set(config.labels.all()) == set([label])
        assert set(config.instance_groups.all()) == set([default_instance_group])

    def test_survey_passwords_ignored(self, inventory_source):
        iu = inventory_source.create_unified_job(survey_passwords={'foo': '$encrypted$'})
        assert iu.launch_config.prompts_dict() == {}


@pytest.fixture
def full_prompts_dict(inventory, credential, label, default_instance_group):
    ee = ExecutionEnvironment.objects.create(name='test-ee', image='quay.io/foo/bar')
    r = {
        'limit': 'foobar',
        'inventory': inventory,
        'credentials': [credential],
        'execution_environment': ee,
        'labels': [label],
        'instance_groups': [default_instance_group],
        'verbosity': 3,
        'scm_branch': 'non_dev',
        'diff_mode': True,
        'skip_tags': 'foobar',
        'job_tags': 'untagged',
        'forks': 26,
        'job_slice_count': 2,
        'timeout': 200,
        'extra_vars': {'prompted_key': 'prompted_val'},
        'job_type': 'check',
    }
    assert set(JobTemplate.get_ask_mapping().keys()) - set(r.keys()) == set()  # make fixture comprehensive
    return r


@pytest.mark.django_db
def test_config_reversibility(full_jt, full_prompts_dict):
    """
    Checks that a blob of saved prompts will be re-created in the
    prompts_dict for launching new jobs
    """
    config = full_jt.create_unified_job(**full_prompts_dict).launch_config
    assert config.prompts_dict() == full_prompts_dict


@pytest.mark.django_db
class TestLaunchConfigModels:
    def get_concrete_subclasses(self, cls):
        r = []
        for c in cls.__subclasses__():
            if c._meta.abstract:
                r.extend(self.get_concrete_subclasses(c))
            else:
                r.append(c)
        return r

    def test_non_job_config_complete(self):
        """This performs model validation which replaces code that used run on import."""
        for field_name in JobTemplate.get_ask_mapping().keys():
            if field_name in LaunchTimeConfigBase.SUBCLASS_FIELDS:
                assert not hasattr(LaunchTimeConfigBase, field_name)
            else:
                assert hasattr(LaunchTimeConfigBase, field_name)

    def test_subclass_fields_complete(self):
        for cls in self.get_concrete_subclasses(LaunchTimeConfigBase):
            for field_name in LaunchTimeConfigBase.SUBCLASS_FIELDS:
                assert hasattr(cls, field_name)
