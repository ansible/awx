import warnings
from unittest.mock import Mock, patch

from awx.api.schema import CustomAutoSchema


class TestCustomAutoSchema:
    """Unit tests for CustomAutoSchema class."""

    def test_get_tags_with_swagger_topic(self):
        """Test get_tags returns swagger_topic when available."""
        view = Mock()
        view.swagger_topic = 'custom_topic'
        view.get_serializer = Mock(return_value=Mock())

        schema = CustomAutoSchema()
        schema.view = view

        tags = schema.get_tags()
        assert tags == ['Custom_Topic']

    def test_get_tags_with_serializer_meta_model(self):
        """Test get_tags returns model verbose_name_plural from serializer."""
        # Create a mock model with verbose_name_plural
        mock_model = Mock()
        mock_model._meta.verbose_name_plural = 'test models'

        # Create a mock serializer with Meta.model
        mock_serializer = Mock()
        mock_serializer.Meta.model = mock_model

        view = Mock(spec=[])  # View without swagger_topic
        view.get_serializer = Mock(return_value=mock_serializer)

        schema = CustomAutoSchema()
        schema.view = view

        tags = schema.get_tags()
        assert tags == ['Test Models']

    def test_get_tags_with_view_model(self):
        """Test get_tags returns model verbose_name_plural from view."""
        # Create a mock model with verbose_name_plural
        mock_model = Mock()
        mock_model._meta.verbose_name_plural = 'view models'

        view = Mock(spec=['model'])  # View without swagger_topic or get_serializer
        view.model = mock_model

        schema = CustomAutoSchema()
        schema.view = view

        tags = schema.get_tags()
        assert tags == ['View Models']

    def test_get_tags_without_get_serializer(self):
        """Test get_tags when view doesn't have get_serializer method."""
        mock_model = Mock()
        mock_model._meta.verbose_name_plural = 'test objects'

        view = Mock(spec=['model'])
        view.model = mock_model

        schema = CustomAutoSchema()
        schema.view = view

        tags = schema.get_tags()
        assert tags == ['Test Objects']

    def test_get_tags_serializer_exception_with_warning(self):
        """Test get_tags handles exception in get_serializer with warning."""
        mock_model = Mock()
        mock_model._meta.verbose_name_plural = 'fallback models'

        view = Mock(spec=['get_serializer', 'model', '__class__'])
        view.__class__.__name__ = 'TestView'
        view.get_serializer = Mock(side_effect=Exception('Serializer error'))
        view.model = mock_model

        schema = CustomAutoSchema()
        schema.view = view

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            tags = schema.get_tags()

            # Check that a warning was raised
            assert len(w) == 1
            assert 'TestView.get_serializer() raised an exception' in str(w[0].message)

        # Should still get tags from view.model
        assert tags == ['Fallback Models']

    def test_get_tags_serializer_without_meta_model(self):
        """Test get_tags when serializer doesn't have Meta.model."""
        mock_serializer = Mock(spec=[])  # No Meta attribute

        view = Mock(spec=['get_serializer'])
        view.__class__.__name__ = 'NoMetaView'
        view.get_serializer = Mock(return_value=mock_serializer)

        schema = CustomAutoSchema()
        schema.view = view

        with patch.object(CustomAutoSchema.__bases__[0], 'get_tags', return_value=['Default Tag']) as mock_super:
            tags = schema.get_tags()
            mock_super.assert_called_once()
            assert tags == ['Default Tag']

    def test_get_tags_fallback_to_super(self):
        """Test get_tags falls back to parent class method."""
        view = Mock(spec=['get_serializer'])
        view.get_serializer = Mock(return_value=Mock(spec=[]))

        schema = CustomAutoSchema()
        schema.view = view

        with patch.object(CustomAutoSchema.__bases__[0], 'get_tags', return_value=['Super Tag']) as mock_super:
            tags = schema.get_tags()
            mock_super.assert_called_once()
            assert tags == ['Super Tag']

    def test_get_tags_empty_with_warning(self):
        """Test get_tags returns 'api' fallback when no tags can be determined."""
        view = Mock(spec=['get_serializer'])
        view.__class__.__name__ = 'EmptyView'
        view.get_serializer = Mock(return_value=Mock(spec=[]))

        schema = CustomAutoSchema()
        schema.view = view

        with patch.object(CustomAutoSchema.__bases__[0], 'get_tags', return_value=[]):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                tags = schema.get_tags()

                # Check that a warning was raised
                assert len(w) == 1
                assert 'Could not determine tags for EmptyView' in str(w[0].message)

            # Should fallback to 'api'
            assert tags == ['api']

    def test_get_tags_swagger_topic_title_case(self):
        """Test that swagger_topic is properly title-cased."""
        view = Mock()
        view.swagger_topic = 'multi_word_topic'
        view.get_serializer = Mock(return_value=Mock())

        schema = CustomAutoSchema()
        schema.view = view

        tags = schema.get_tags()
        assert tags == ['Multi_Word_Topic']

    def test_is_deprecated_true(self):
        """Test is_deprecated returns True when view has deprecated=True."""
        view = Mock()
        view.deprecated = True

        schema = CustomAutoSchema()
        schema.view = view

        assert schema.is_deprecated() is True

    def test_is_deprecated_false(self):
        """Test is_deprecated returns False when view has deprecated=False."""
        view = Mock()
        view.deprecated = False

        schema = CustomAutoSchema()
        schema.view = view

        assert schema.is_deprecated() is False

    def test_is_deprecated_missing_attribute(self):
        """Test is_deprecated returns False when view doesn't have deprecated attribute."""
        view = Mock(spec=[])

        schema = CustomAutoSchema()
        schema.view = view

        assert schema.is_deprecated() is False

    def test_get_tags_serializer_meta_without_model(self):
        """Test get_tags when serializer has Meta but no model attribute."""
        mock_serializer = Mock()
        mock_serializer.Meta = Mock(spec=[])  # Meta exists but no model

        mock_model = Mock()
        mock_model._meta.verbose_name_plural = 'backup models'

        view = Mock(spec=['get_serializer', 'model'])
        view.get_serializer = Mock(return_value=mock_serializer)
        view.model = mock_model

        schema = CustomAutoSchema()
        schema.view = view

        tags = schema.get_tags()
        # Should fall back to view.model
        assert tags == ['Backup Models']

    def test_get_tags_complex_scenario_exception_recovery(self):
        """Test complex scenario where serializer fails but view.model exists."""
        mock_model = Mock()
        mock_model._meta.verbose_name_plural = 'recovery models'

        view = Mock(spec=['get_serializer', 'model', '__class__'])
        view.__class__.__name__ = 'ComplexView'
        view.get_serializer = Mock(side_effect=ValueError('Invalid serializer'))
        view.model = mock_model

        schema = CustomAutoSchema()
        schema.view = view

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            tags = schema.get_tags()

            # Should have warned about the exception
            assert len(w) == 1
            assert 'ComplexView.get_serializer() raised an exception' in str(w[0].message)

        # But still recovered and got tags from view.model
        assert tags == ['Recovery Models']

    def test_get_tags_priority_order(self):
        """Test that get_tags respects priority: swagger_topic > serializer.Meta.model > view.model."""
        # Set up a view with all three options
        mock_model_view = Mock()
        mock_model_view._meta.verbose_name_plural = 'view models'

        mock_model_serializer = Mock()
        mock_model_serializer._meta.verbose_name_plural = 'serializer models'

        mock_serializer = Mock()
        mock_serializer.Meta.model = mock_model_serializer

        view = Mock()
        view.swagger_topic = 'priority_topic'
        view.get_serializer = Mock(return_value=mock_serializer)
        view.model = mock_model_view

        schema = CustomAutoSchema()
        schema.view = view

        tags = schema.get_tags()
        # swagger_topic should take priority
        assert tags == ['Priority_Topic']
