import pytest

from awx.api.versioning import reverse
from awx.main import models


@pytest.mark.django_db
def test_aliased_forward_reverse_field_searches(instance, options, get, admin):
    url = reverse('api:unified_job_template_list')
    response = options(url, None, admin)
    assert 'job_template__search' in response.data['related_search_fields']
    get(reverse("api:unified_job_template_list") + "?job_template__search=anything", user=admin, expect=200)


@pytest.mark.django_db
@pytest.mark.parametrize('model', (
    'Project',
    'JobTemplate',
    'WorkflowJobTemplate'
))
class TestUnifiedOrganization:

    def data_for_model(self, model, orm_style=False):
        data = {
            'name': 'foo',
            'organization': None
        }
        if model == 'JobTemplate':
            proj = models.Project.objects.create(
                name="test-proj",
                playbook_files=['helloworld.yml']
            )
            if orm_style:
                data['project_id'] = proj.id
            else:
                data['project'] = proj.id
            data['playbook'] = 'helloworld.yml'
            data['ask_inventory_on_launch'] = True
        return data

    def test_organization_blank_on_edit_of_orphan(self, model, admin_user, patch):
        cls = getattr(models, model)
        data = self.data_for_model(model, orm_style=True)
        obj = cls.objects.create(**data)
        patch(
            url=obj.get_absolute_url(),
            data={'name': 'foooooo'},
            user=admin_user,
            expect=200
        )
        obj.refresh_from_db()
        assert obj.name == 'foooooo'

    def test_organization_blank_on_edit_of_orphan_as_nonsuperuser(self, model, rando, patch):
        """Test case reflects historical bug where ordinary users got weird error
        message when editing an orphaned project
        """
        cls = getattr(models, model)
        data = self.data_for_model(model, orm_style=True)
        obj = cls.objects.create(**data)
        if model == 'JobTemplate':
            obj.project.admin_role.members.add(rando)
        obj.admin_role.members.add(rando)
        patch(
            url=obj.get_absolute_url(),
            data={'name': 'foooooo'},
            user=rando,
            expect=200
        )
        obj.refresh_from_db()
        assert obj.name == 'foooooo'

    def test_organization_blank_on_edit_of_normal(self, model, admin_user, patch, organization):
        cls = getattr(models, model)
        data = self.data_for_model(model, orm_style=True)
        data['organization'] = organization
        obj = cls.objects.create(**data)
        patch(
            url=obj.get_absolute_url(),
            data={'name': 'foooooo'},
            user=admin_user,
            expect=200
        )
        obj.refresh_from_db()
        assert obj.name == 'foooooo'
