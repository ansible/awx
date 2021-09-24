import pytest


def test_image_unchanged_no_delete_task(execution_environment, mocker):
    """When an irrelevant EE field is changed, we do not run the image cleanup task"""
    execution_environment.description = 'foobar'
    with mocker.patch() as p:
        execution_environment.save()
        p.assert_not_called()
