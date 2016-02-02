import pytest

from awx.main.models.organization import Organization

@pytest.fixture
def organization():
    return Organization.objects.create(name="test-org", description="test-org-desc")

@pytest.fixture
def permissions():
    return {
        'admin':{'create':True, 'read':True, 'write':True,
                 'update':True, 'delete':True, 'scm_update':True, 'execute':True, 'use':True,},

        'auditor':{'read':True, 'create':False, 'write':False,
                   'update':False, 'delete':False, 'scm_update':False, 'execute':False, 'use':False,},
    }

