# Python
import pytest

# Django Rest Framework
from rest_framework.exceptions import ValidationError

# AWX
from awx.api.serializers import JobLaunchSerializer


def test_primary_key_related_field():
    # We are testing if the PrimaryKeyRelatedField in this serializer can take dictionary.
    # PrimaryKeyRelatedField should not be able to take dictionary as input, and should raise a ValidationError.
    data = {'credentials' : {'1': '2', '3':'4'}}
    with pytest.raises(ValidationError):
        JobLaunchSerializer(data=data)
