import pytest
import json
from awx.main.models import (
    Project,
)
from django.core.exceptions import ValidationError


def test_clean_credential_insights():
    proj = Project(name="myproj", credential=None, scm_type='insights')
    with pytest.raises(ValidationError) as e:
        proj.clean_credential()

    assert json.dumps(str(e.value)) == json.dumps(str([u'Insights Credential is required for an Insights Project.']))

