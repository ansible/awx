import pytest

from django.core.urlresolvers import reverse


#
# user creation
#

@pytest.mark.django_db
def test_user_create(post, admin):
    response = post(reverse('api:user_list'), {
        "username": "affable",
        "first_name": "a",
        "last_name": "a",
        "email": "a@a.com",
        "is_superuser": False,
        "password": "fo0m4nchU"
    }, admin)
    assert response.status_code == 201

@pytest.mark.django_db
def test_fail_double_create_user(post, admin):
    response = post(reverse('api:user_list'), {
        "username": "affable",
        "first_name": "a",
        "last_name": "a",
        "email": "a@a.com",
        "is_superuser": False,
        "password": "fo0m4nchU"
    }, admin)
    assert response.status_code == 201

    response = post(reverse('api:user_list'), {
        "username": "affable",
        "first_name": "a",
        "last_name": "a",
        "email": "a@a.com",
        "is_superuser": False,
        "password": "fo0m4nchU"
    }, admin)
    assert response.status_code == 400

@pytest.mark.django_db
def test_create_delete_create_user(post, delete, admin):
    response = post(reverse('api:user_list'), {
        "username": "affable",
        "first_name": "a",
        "last_name": "a",
        "email": "a@a.com",
        "is_superuser": False,
        "password": "fo0m4nchU"
    }, admin)
    assert response.status_code == 201

    response = delete(reverse('api:user_detail', args=(response.data['id'],)), admin)
    assert response.status_code == 204

    response = post(reverse('api:user_list'), {
        "username": "affable",
        "first_name": "a",
        "last_name": "a",
        "email": "a@a.com",
        "is_superuser": False,
        "password": "fo0m4nchU"
    }, admin)
    print(response.data)
    assert response.status_code == 201

@pytest.mark.django_db
def test_add_user_admin_role_member(post, user):
    admin = user('admin', is_superuser=True)
    normal = user('normal')

    url = reverse('api:user_roles_list', args=(admin.pk,))
    response = post(url, {'id':normal.admin_role.pk}, admin)
    assert response.status_code == 403
    assert 'not change the membership' in response.rendered_content
