from awx.main.tasks import run_label_cleanup

def test_run_label_cleanup(mocker):
    qs = mocker.Mock(**{'count.return_value': 3, 'delete.return_value': None})
    mock_label = mocker.patch('awx.main.models.label.Label.get_orphaned_labels',return_value=qs)

    ret = run_label_cleanup()

    mock_label.assert_called_with()
    qs.delete.assert_called_with()
    assert 3 == ret

