from awx.main.models.label import Label

def test_get_orphaned_labels(mocker):
    mock_query_set = mocker.MagicMock()
    Label.objects.filter = mocker.MagicMock(return_value=mock_query_set)

    ret = Label.get_orphaned_labels()

    assert mock_query_set == ret
    Label.objects.filter.assert_called_with(organization=None, jobtemplate_labels__isnull=True)

def test_is_detached(mocker):
    mock_query_set = mocker.MagicMock()
    Label.objects.filter = mocker.MagicMock(return_value=mock_query_set)
    mock_query_set.count.return_value = 1

    ret = Label.is_detached(37)

    assert ret is True
    Label.objects.filter.assert_called_with(id=37, unifiedjob_labels__isnull=True, unifiedjobtemplate_labels__isnull=True)
    mock_query_set.count.assert_called_with()

def test_is_detached_not(mocker):
    mock_query_set = mocker.MagicMock()
    Label.objects.filter = mocker.MagicMock(return_value=mock_query_set)
    mock_query_set.count.return_value = 0

    ret = Label.is_detached(37)

    assert ret is False
    Label.objects.filter.assert_called_with(id=37, unifiedjob_labels__isnull=True, unifiedjobtemplate_labels__isnull=True)
    mock_query_set.count.assert_called_with()
