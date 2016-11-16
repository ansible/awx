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
