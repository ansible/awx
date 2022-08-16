# Python
import pytest

# Django Rest Framework
from rest_framework.exceptions import ValidationError

# AWX
from awx.api.serializers import JobLaunchSerializer


@pytest.mark.parametrize(
    "param",
    [
        ('credentials'),
        ('instance_groups'),
        ('labels'),
    ],
)
def test_primary_key_related_field(param):
    # We are testing if the PrimaryKeyRelatedField in this serializer can take dictionary.
    # PrimaryKeyRelatedField should not be able to take dictionary as input, and should raise a ValidationError.
    data = {param: {'1': '2', '3': '4'}}
    with pytest.raises(ValidationError):
        JobLaunchSerializer(data=data)
