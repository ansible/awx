
# Python
import pytest

# DRF
from rest_framework import status
from rest_framework.response import Response

# AWX
from awx.api.generics import ParentMixin, SubListCreateAttachDetachAPIView

@pytest.fixture
def get_object_or_404(mocker):
    # pytest patch without return_value generates a random value, we are counting on this
    return mocker.patch('awx.api.generics.get_object_or_404')

@pytest.fixture
def get_object_or_400(mocker):
    return mocker.patch('awx.api.generics.get_object_or_400')

@pytest.fixture
def mock_response_new(mocker):
    m = mocker.patch('awx.api.generics.Response.__new__')
    m.return_value = m
    return m

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

# TODO: Test create and associate failure (i.e. id doesn't exist or record already exists)
# TODO: Mock and check return (Response)
class TestSubListCreateAttachDetachAPIView:
    def test_attach_create_and_associate(self, mocker, get_object_or_400, parent_relationship_factory, mock_response_new):
        (serializer, mock_parent_relationship) = parent_relationship_factory(SubListCreateAttachDetachAPIView, 'wife')
        create_return_value = mocker.MagicMock(status_code=status.HTTP_201_CREATED)
        serializer.create = mocker.Mock(return_value=create_return_value)

        mock_request = mocker.MagicMock(data=dict())
        ret = serializer.attach(mock_request, None, None)

        assert ret == mock_response_new
        serializer.create.assert_called_with(mock_request, None, None)
        mock_parent_relationship.wife.add.assert_called_with(get_object_or_400.return_value)
        mock_response_new.assert_called_with(Response, create_return_value.data, status=status.HTTP_201_CREATED, headers={'Location': create_return_value['Location']})

    def test_attach_associate_only(self, mocker, get_object_or_400, parent_relationship_factory, mock_response_new):
        (serializer, mock_parent_relationship) = parent_relationship_factory(SubListCreateAttachDetachAPIView, 'wife')
        serializer.create = mocker.Mock(return_value=mocker.MagicMock())

        mock_request = mocker.MagicMock(data=dict(id=1))
        ret = serializer.attach(mock_request, None, None)

        assert ret == mock_response_new
        serializer.create.assert_not_called()
        mock_parent_relationship.wife.add.assert_called_with(get_object_or_400.return_value)
        mock_response_new.assert_called_with(Response, status=status.HTTP_204_NO_CONTENT)

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
       
