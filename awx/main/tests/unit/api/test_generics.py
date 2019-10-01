
# Python
import pytest
from unittest import mock

# DRF
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

# AWX
from awx.api.generics import (
    ParentMixin,
    SubListCreateAttachDetachAPIView, SubListAttachDetachAPIView,
    ResourceAccessList,
    ListAPIView
)
from awx.main.models import Organization, Credential


@pytest.fixture
def get_object_or_404(mocker):
    # pytest patch without return_value generates a random value, we are counting on this
    return mocker.patch('awx.api.generics.get_object_or_404')


@pytest.fixture
def get_object_or_400(mocker):
    return mocker.patch('awx.api.generics.get_object_or_400')


@pytest.fixture
def mock_organization():
    return Organization(pk=4, name="Unsaved Org")


@pytest.fixture
def parent_relationship_factory(mocker):
    def rf(serializer_class, relationship_name, relationship_value=mocker.Mock()):
        mock_parent_relationship = mocker.MagicMock(**{'%s.add.return_value' % relationship_name: relationship_value})
        mocker.patch('awx.api.generics.ParentMixin.get_parent_object', return_value=mock_parent_relationship)

        serializer = serializer_class()
        [setattr(serializer, x, '') for x in ['relationship', 'model', 'parent_model']]
        serializer.relationship = relationship_name

        return (serializer, mock_parent_relationship)
    return rf


# TODO: Test create and associate failure (i.e. id doesn't exist, record already exists, permission denied)
# TODO: Mock and check return (Response)
class TestSubListCreateAttachDetachAPIView:
    def test_attach_validate_ok(self, mocker):
        mock_request = mocker.MagicMock(data=dict(id=1))
        serializer = SubListCreateAttachDetachAPIView()

        (sub_id, res) = serializer.attach_validate(mock_request)

        assert sub_id == 1
        assert res is None

    def test_attach_validate_invalid_type(self, mocker):
        mock_request = mocker.MagicMock(data=dict(id='foobar'))
        serializer = SubListCreateAttachDetachAPIView()

        (sub_id, res) = serializer.attach_validate(mock_request)

        assert type(res) is Response

    def test_attach_create_and_associate(self, mocker, get_object_or_400, parent_relationship_factory):
        (serializer, mock_parent_relationship) = parent_relationship_factory(SubListCreateAttachDetachAPIView, 'wife')
        create_return_value = mocker.MagicMock(status_code=status.HTTP_201_CREATED)
        serializer.create = mocker.Mock(return_value=create_return_value)

        mock_request = mocker.MagicMock(data=dict())
        serializer.attach(mock_request, None, None)

        serializer.create.assert_called_with(mock_request, None, None)
        mock_parent_relationship.wife.add.assert_called_with(get_object_or_400.return_value)

    def test_attach_associate_only(self, mocker, get_object_or_400, parent_relationship_factory):
        (serializer, mock_parent_relationship) = parent_relationship_factory(SubListCreateAttachDetachAPIView, 'wife')
        serializer.create = mocker.Mock(return_value=mocker.MagicMock())

        mock_request = mocker.MagicMock(data=dict(id=1))
        serializer.attach(mock_request, None, None)

        serializer.create.assert_not_called()
        mock_parent_relationship.wife.add.assert_called_with(get_object_or_400.return_value)

    def test_unattach_validate_ok(self, mocker):
        mock_request = mocker.MagicMock(data=dict(id=1))
        serializer = SubListCreateAttachDetachAPIView()

        (sub_id, res) = serializer.unattach_validate(mock_request)

        assert sub_id == 1
        assert res is None

    def test_unattach_validate_invalid_type(self, mocker):
        mock_request = mocker.MagicMock(data=dict(id='foobar'))
        serializer = SubListCreateAttachDetachAPIView()

        (sub_id, res) = serializer.unattach_validate(mock_request)

        assert type(res) is Response

    def test_unattach_validate_missing_id(self, mocker):
        mock_request = mocker.MagicMock(data=dict())
        serializer = SubListCreateAttachDetachAPIView()

        (sub_id, res) = serializer.unattach_validate(mock_request)

        assert sub_id is None
        assert type(res) is Response

    def test_unattach_by_id_ok(self, mocker, parent_relationship_factory, get_object_or_400):
        (serializer, mock_parent_relationship) = parent_relationship_factory(SubListCreateAttachDetachAPIView, 'wife')
        mock_request = mocker.MagicMock()
        mock_sub = mocker.MagicMock(name="object to unattach")
        get_object_or_400.return_value = mock_sub

        res = serializer.unattach_by_id(mock_request, 1)

        assert type(res) is Response
        assert res.status_code == status.HTTP_204_NO_CONTENT
        mock_parent_relationship.wife.remove.assert_called_with(mock_sub)

    def test_unattach_ok(self, mocker):
        mock_request = mocker.MagicMock()
        mock_sub_id = mocker.MagicMock()
        view = SubListCreateAttachDetachAPIView()
        view.unattach_validate = mocker.MagicMock()
        view.unattach_by_id = mocker.MagicMock()
        view.unattach_validate.return_value = (mock_sub_id, None)

        view.unattach(mock_request)

        view.unattach_validate.assert_called_with(mock_request)
        view.unattach_by_id.assert_called_with(mock_request, mock_sub_id)

    def test_unattach_invalid(self, mocker):
        mock_request = mocker.MagicMock()
        mock_res = mocker.MagicMock()
        view = SubListCreateAttachDetachAPIView()
        view.unattach_validate = mocker.MagicMock()
        view.unattach_by_id = mocker.MagicMock()
        view.unattach_validate.return_value = (None, mock_res)

        view.unattach(mock_request)

        view.unattach_validate.assert_called_with(mock_request)
        view.unattach_by_id.assert_not_called()


def test_attach_detatch_only(mocker):
    mock_request = mocker.MagicMock()
    mock_request.data = {'name': 'name for my new model'}
    view = SubListAttachDetachAPIView()
    view.model = mocker.MagicMock()
    view.model._meta = mocker.MagicMock()
    view.model._meta.verbose_name = "Foo Bar"

    resp = view.post(mock_request)

    assert 'Foo Bar' in resp.data['msg']
    assert 'field is missing' in resp.data['msg']


class TestParentMixin:
    def test_get_parent_object(self, mocker, get_object_or_404):
        parent_mixin = ParentMixin()
        parent_mixin.lookup_field = 'foo'
        parent_mixin.kwargs = dict(foo='bar')
        parent_mixin.parent_model = 'parent_model'
        mock_parent_mixin = mocker.MagicMock(wraps=parent_mixin)

        return_value = mock_parent_mixin.get_parent_object()

        get_object_or_404.assert_called_with(parent_mixin.parent_model, **parent_mixin.kwargs)
        assert get_object_or_404.return_value == return_value


class TestResourceAccessList:

    def mock_request(self):
        return mock.MagicMock(
            user=mock.MagicMock(is_anonymous=False, is_superuser=False),
            method='GET')

    def mock_view(self, parent=None):
        view = ResourceAccessList()
        view.parent_model = Organization
        view.kwargs = {'pk': 4}
        if parent:
            view.get_parent_object = lambda: parent
        return view

    def test_parent_access_check_failed(self, mocker, mock_organization):
        mock_access = mocker.MagicMock(__name__='for logger', return_value=False)
        with mocker.patch('awx.main.access.BaseAccess.can_read', mock_access):
            with pytest.raises(PermissionDenied):
                self.mock_view(parent=mock_organization).check_permissions(self.mock_request())
            mock_access.assert_called_once_with(mock_organization)

    def test_parent_access_check_worked(self, mocker, mock_organization):
        mock_access = mocker.MagicMock(__name__='for logger', return_value=True)
        with mocker.patch('awx.main.access.BaseAccess.can_read', mock_access):
            self.mock_view(parent=mock_organization).check_permissions(self.mock_request())
            mock_access.assert_called_once_with(mock_organization)


def test_related_search_reverse_FK_field():
    view = ListAPIView()
    view.model = Credential
    assert 'unifiedjobtemplates__search' in view.related_search_fields
