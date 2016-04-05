from awx.main.models.label import Label

def test_get_orphaned_labels(mocker):
    mock_query_set = mocker.MagicMock()
    Label.objects.filter = mocker.MagicMock(return_value=mock_query_set)

    ret = Label.get_orphaned_labels()

    assert mock_query_set == ret
    Label.objects.filter.assert_called_with(organization=None, jobtemplate_labels__isnull=True)
