import pytest

from awx.api.versioning import reverse
from awx.main.models.mixins import WebhookTemplateMixin
from awx.main.models.credential import Credential, CredentialType


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_role, expect", [
        ('superuser', 200),
        ('org admin', 200),
        ('jt admin', 200),
        ('jt execute', 403),
        ('org member', 403),
    ]
)
def test_get_webhook_key_jt(organization_factory, job_template_factory, get, user_role, expect):
    objs = organization_factory("org", superusers=['admin'], users=['user'])
    jt = job_template_factory("jt", organization=objs.organization,
                              inventory='test_inv', project='test_proj').job_template
    if user_role == 'superuser':
        user = objs.superusers.admin
    else:
        user = objs.users.user
        grant_obj = objs.organization if user_role.startswith('org') else jt
        getattr(grant_obj, '{}_role'.format(user_role.split()[1])).members.add(user)

    url = reverse('api:webhook_key', kwargs={'model_kwarg': 'job_templates', 'pk': jt.pk})
    response = get(url, user=user, expect=expect)
    if expect < 400:
        assert response.data == {'webhook_key': ''}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_role, expect", [
        ('superuser', 200),
        ('org admin', 200),
        ('jt admin', 200),
        ('jt execute', 403),
        ('org member', 403),
    ]
)
def test_get_webhook_key_wfjt(organization_factory, workflow_job_template_factory, get, user_role, expect):
    objs = organization_factory("org", superusers=['admin'], users=['user'])
    wfjt = workflow_job_template_factory("wfjt", organization=objs.organization).workflow_job_template
    if user_role == 'superuser':
        user = objs.superusers.admin
    else:
        user = objs.users.user
        grant_obj = objs.organization if user_role.startswith('org') else wfjt
        getattr(grant_obj, '{}_role'.format(user_role.split()[1])).members.add(user)

    url = reverse('api:webhook_key', kwargs={'model_kwarg': 'workflow_job_templates', 'pk': wfjt.pk})
    response = get(url, user=user, expect=expect)
    if expect < 400:
        assert response.data == {'webhook_key': ''}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_role, expect", [
        ('superuser', 201),
        ('org admin', 201),
        ('jt admin', 201),
        ('jt execute', 403),
        ('org member', 403),
    ]
)
def test_post_webhook_key_jt(organization_factory, job_template_factory, post, user_role, expect):
    objs = organization_factory("org", superusers=['admin'], users=['user'])
    jt = job_template_factory("jt", organization=objs.organization,
                              inventory='test_inv', project='test_proj').job_template
    if user_role == 'superuser':
        user = objs.superusers.admin
    else:
        user = objs.users.user
        grant_obj = objs.organization if user_role.startswith('org') else jt
        getattr(grant_obj, '{}_role'.format(user_role.split()[1])).members.add(user)

    url = reverse('api:webhook_key', kwargs={'model_kwarg': 'job_templates', 'pk': jt.pk})
    response = post(url, {}, user=user, expect=expect)
    if expect < 400:
        assert bool(response.data.get('webhook_key'))


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_role, expect", [
        ('superuser', 201),
        ('org admin', 201),
        ('jt admin', 201),
        ('jt execute', 403),
        ('org member', 403),
    ]
)
def test_post_webhook_key_wfjt(organization_factory, workflow_job_template_factory, post, user_role, expect):
    objs = organization_factory("org", superusers=['admin'], users=['user'])
    wfjt = workflow_job_template_factory("wfjt", organization=objs.organization).workflow_job_template
    if user_role == 'superuser':
        user = objs.superusers.admin
    else:
        user = objs.users.user
        grant_obj = objs.organization if user_role.startswith('org') else wfjt
        getattr(grant_obj, '{}_role'.format(user_role.split()[1])).members.add(user)

    url = reverse('api:webhook_key', kwargs={'model_kwarg': 'workflow_job_templates', 'pk': wfjt.pk})
    response = post(url, {}, user=user, expect=expect)
    if expect < 400:
        assert bool(response.data.get('webhook_key'))


@pytest.mark.django_db
@pytest.mark.parametrize(
    "service", [s for s, _ in WebhookTemplateMixin.SERVICES]
)
def test_set_webhook_service(organization_factory, job_template_factory, patch, service):
    objs = organization_factory("org", superusers=['admin'])
    jt = job_template_factory("jt", organization=objs.organization,
                              inventory='test_inv', project='test_proj').job_template
    admin = objs.superusers.admin
    assert (jt.webhook_service, jt.webhook_key) == ('', '')

    url = reverse('api:job_template_detail', kwargs={'pk': jt.pk})
    patch(url, {'webhook_service': service}, user=admin, expect=200)
    jt.refresh_from_db()

    assert jt.webhook_service == service
    assert jt.webhook_key != ''


@pytest.mark.django_db
@pytest.mark.parametrize(
    "service", [s for s, _ in WebhookTemplateMixin.SERVICES]
)
def test_unset_webhook_service(organization_factory, job_template_factory, patch, service):
    objs = organization_factory("org", superusers=['admin'])
    jt = job_template_factory("jt", organization=objs.organization, webhook_service=service,
                              inventory='test_inv', project='test_proj').job_template
    admin = objs.superusers.admin
    assert jt.webhook_service == service
    assert jt.webhook_key != ''

    url = reverse('api:job_template_detail', kwargs={'pk': jt.pk})
    patch(url, {'webhook_service': ''}, user=admin, expect=200)
    jt.refresh_from_db()

    assert (jt.webhook_service, jt.webhook_key) == ('', '')


@pytest.mark.django_db
@pytest.mark.parametrize(
    "service", [s for s, _ in WebhookTemplateMixin.SERVICES]
)
def test_set_webhook_credential(organization_factory, job_template_factory, patch, service):
    objs = organization_factory("org", superusers=['admin'])
    jt = job_template_factory("jt", organization=objs.organization, webhook_service=service,
                              inventory='test_inv', project='test_proj').job_template
    admin = objs.superusers.admin
    assert jt.webhook_service == service
    assert jt.webhook_key != ''

    cred_type = CredentialType.defaults['{}_token'.format(service)]()
    cred_type.save()
    cred = Credential.objects.create(credential_type=cred_type, name='test-cred',
                                     inputs={'token': 'secret'})

    url = reverse('api:job_template_detail', kwargs={'pk': jt.pk})
    patch(url, {'webhook_credential': cred.pk}, user=admin, expect=200)
    jt.refresh_from_db()

    assert jt.webhook_service == service
    assert jt.webhook_key != ''
    assert jt.webhook_credential == cred


@pytest.mark.django_db
@pytest.mark.parametrize(
    "service,token", [
        (s, WebhookTemplateMixin.SERVICES[i - 1][0]) for i, (s, _) in enumerate(WebhookTemplateMixin.SERVICES)
    ]
)
def test_set_wrong_service_webhook_credential(organization_factory, job_template_factory, patch, service, token):
    objs = organization_factory("org", superusers=['admin'])
    jt = job_template_factory("jt", organization=objs.organization, webhook_service=service,
                              inventory='test_inv', project='test_proj').job_template
    admin = objs.superusers.admin
    assert jt.webhook_service == service
    assert jt.webhook_key != ''

    cred_type = CredentialType.defaults['{}_token'.format(token)]()
    cred_type.save()
    cred = Credential.objects.create(credential_type=cred_type, name='test-cred',
                                     inputs={'token': 'secret'})

    url = reverse('api:job_template_detail', kwargs={'pk': jt.pk})
    response = patch(url, {'webhook_credential': cred.pk}, user=admin, expect=400)
    jt.refresh_from_db()

    assert jt.webhook_service == service
    assert jt.webhook_key != ''
    assert jt.webhook_credential is None
    assert response.data == {'webhook_credential': ["Must match the selected webhook service."]}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "service", [s for s, _ in WebhookTemplateMixin.SERVICES]
)
def test_set_webhook_credential_without_service(organization_factory, job_template_factory, patch, service):
    objs = organization_factory("org", superusers=['admin'])
    jt = job_template_factory("jt", organization=objs.organization,
                              inventory='test_inv', project='test_proj').job_template
    admin = objs.superusers.admin
    assert jt.webhook_service == ''
    assert jt.webhook_key == ''

    cred_type = CredentialType.defaults['{}_token'.format(service)]()
    cred_type.save()
    cred = Credential.objects.create(credential_type=cred_type, name='test-cred',
                                     inputs={'token': 'secret'})

    url = reverse('api:job_template_detail', kwargs={'pk': jt.pk})
    response = patch(url, {'webhook_credential': cred.pk}, user=admin, expect=400)
    jt.refresh_from_db()

    assert jt.webhook_service == ''
    assert jt.webhook_key == ''
    assert jt.webhook_credential is None
    assert response.data == {'webhook_credential': ["Must match the selected webhook service."]}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "service", [s for s, _ in WebhookTemplateMixin.SERVICES]
)
def test_unset_webhook_service_with_credential(organization_factory, job_template_factory, patch, service):
    objs = organization_factory("org", superusers=['admin'])
    jt = job_template_factory("jt", organization=objs.organization, webhook_service=service,
                              inventory='test_inv', project='test_proj').job_template
    admin = objs.superusers.admin
    assert jt.webhook_service == service
    assert jt.webhook_key != ''

    cred_type = CredentialType.defaults['{}_token'.format(service)]()
    cred_type.save()
    cred = Credential.objects.create(credential_type=cred_type, name='test-cred',
                                     inputs={'token': 'secret'})
    jt.webhook_credential = cred
    jt.save()

    url = reverse('api:job_template_detail', kwargs={'pk': jt.pk})
    response = patch(url, {'webhook_service': ''}, user=admin, expect=400)
    jt.refresh_from_db()

    assert jt.webhook_service == service
    assert jt.webhook_key != ''
    assert jt.webhook_credential == cred
    assert response.data == {'webhook_credential': ["Must match the selected webhook service."]}
