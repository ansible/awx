import pytest
from rest_framework import serializers

from awx.api.serializers import WorkflowJobTemplateNodeSerializer


class TestValidateScmBranch:
    """Regression: scm_branch must not begin with '-' (after stripping
    leading whitespace) to prevent git argument injection."""

    @pytest.mark.parametrize(
        'branch',
        [
            'main',
            'feature/my-branch',
            'v1.0',
            '  main',
            'refs/heads/main',
        ],
    )
    def test_valid_branches_accepted(self, branch):
        serializer = WorkflowJobTemplateNodeSerializer()
        result = serializer.validate_scm_branch(branch)
        assert result == branch

    @pytest.mark.parametrize(
        'branch',
        [
            None,
            '',
        ],
    )
    def test_falsy_branches_accepted(self, branch):
        serializer = WorkflowJobTemplateNodeSerializer()
        result = serializer.validate_scm_branch(branch)
        assert result == branch

    @pytest.mark.parametrize(
        'branch',
        [
            '-flag',
            '--upload-pack=/bin/id',
            '  --upload-pack=/bin/id',
            ' -x',
            '--option=value',
        ],
    )
    def test_branches_starting_with_dash_rejected(self, branch):
        serializer = WorkflowJobTemplateNodeSerializer()
        with pytest.raises(serializers.ValidationError):
            serializer.validate_scm_branch(branch)
