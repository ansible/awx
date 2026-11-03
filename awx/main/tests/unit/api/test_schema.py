import copy
import json
import warnings
from unittest.mock import Mock, mock_open, patch

from rest_framework.permissions import IsAuthenticated

from awx.api.schema import (
    CustomAutoSchema,
    AuthenticatedSpectacularAPIView,
    AuthenticatedSpectacularSwaggerView,
    AuthenticatedSpectacularRedocView,
    filter_credential_type_schema,
    inject_ai_descriptions,
    inject_clean_text_pattern_components,
)


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


class TestAuthenticatedSchemaViews:
    """Unit tests for authenticated schema view classes."""

    def test_authenticated_spectacular_api_view_requires_authentication(self):
        """Test that AuthenticatedSpectacularAPIView requires authentication."""
        assert IsAuthenticated in AuthenticatedSpectacularAPIView.permission_classes

    def test_authenticated_spectacular_swagger_view_requires_authentication(self):
        """Test that AuthenticatedSpectacularSwaggerView requires authentication."""
        assert IsAuthenticated in AuthenticatedSpectacularSwaggerView.permission_classes

    def test_authenticated_spectacular_redoc_view_requires_authentication(self):
        """Test that AuthenticatedSpectacularRedocView requires authentication."""
        assert IsAuthenticated in AuthenticatedSpectacularRedocView.permission_classes


class TestFilterCredentialTypeSchema:
    """Unit tests for filter_credential_type_schema postprocessing hook."""

    def test_filters_both_schemas_correctly(self):
        """Test that both CredentialTypeRequest and PatchedCredentialTypeRequest schemas are filtered."""
        result = {
            'components': {
                'schemas': {
                    'CredentialTypeRequest': {
                        'properties': {
                            'kind': {
                                'enum': [
                                    'ssh',
                                    'vault',
                                    'net',
                                    'scm',
                                    'cloud',
                                    'registry',
                                    'token',
                                    'insights',
                                    'external',
                                    'kubernetes',
                                    'galaxy',
                                    'cryptography',
                                    None,
                                ],
                                'type': 'string',
                            }
                        }
                    },
                    'PatchedCredentialTypeRequest': {
                        'properties': {
                            'kind': {
                                'enum': [
                                    'ssh',
                                    'vault',
                                    'net',
                                    'scm',
                                    'cloud',
                                    'registry',
                                    'token',
                                    'insights',
                                    'external',
                                    'kubernetes',
                                    'galaxy',
                                    'cryptography',
                                    None,
                                ],
                                'type': 'string',
                            }
                        }
                    },
                }
            }
        }

        returned = filter_credential_type_schema(result, None, None, None)

        # POST/PUT schema: no None (required field)
        assert result['components']['schemas']['CredentialTypeRequest']['properties']['kind']['enum'] == ['cloud', 'net']
        assert result['components']['schemas']['CredentialTypeRequest']['properties']['kind']['description'] == "* `cloud` - Cloud\\n* `net` - Network"

        # PATCH schema: includes None (optional field)
        assert result['components']['schemas']['PatchedCredentialTypeRequest']['properties']['kind']['enum'] == ['cloud', 'net', None]
        assert result['components']['schemas']['PatchedCredentialTypeRequest']['properties']['kind']['description'] == "* `cloud` - Cloud\\n* `net` - Network"

        # Other properties should be preserved
        assert result['components']['schemas']['CredentialTypeRequest']['properties']['kind']['type'] == 'string'

        # Function should return the result
        assert returned is result

    def test_handles_empty_result(self):
        """Test graceful handling when result dict is empty."""
        result = {}
        original = copy.deepcopy(result)

        returned = filter_credential_type_schema(result, None, None, None)

        assert result == original
        assert returned is result

    def test_handles_missing_enum(self):
        """Test that schemas without enum key are not modified."""
        result = {'components': {'schemas': {'CredentialTypeRequest': {'properties': {'kind': {'type': 'string', 'description': 'Some description'}}}}}}
        original = copy.deepcopy(result)

        filter_credential_type_schema(result, None, None, None)

        assert result == original

    def test_filters_only_target_schemas(self):
        """Test that only CredentialTypeRequest schemas are modified, not others."""
        result = {
            'components': {
                'schemas': {
                    'CredentialTypeRequest': {'properties': {'kind': {'enum': ['ssh', 'cloud', 'net', None]}}},
                    'OtherSchema': {'properties': {'kind': {'enum': ['option1', 'option2']}}},
                }
            }
        }

        other_schema_before = copy.deepcopy(result['components']['schemas']['OtherSchema'])

        filter_credential_type_schema(result, None, None, None)

        # CredentialTypeRequest should be filtered (no None for required field)
        assert result['components']['schemas']['CredentialTypeRequest']['properties']['kind']['enum'] == ['cloud', 'net']

        # OtherSchema should be unchanged
        assert result['components']['schemas']['OtherSchema'] == other_schema_before

    def test_handles_only_one_schema_present(self):
        """Test that function works when only one target schema is present."""
        result = {'components': {'schemas': {'CredentialTypeRequest': {'properties': {'kind': {'enum': ['ssh', 'cloud', 'net', None]}}}}}}

        filter_credential_type_schema(result, None, None, None)

        assert result['components']['schemas']['CredentialTypeRequest']['properties']['kind']['enum'] == ['cloud', 'net']

    def test_handles_missing_properties(self):
        """Test graceful handling when schema has no properties key."""
        result = {'components': {'schemas': {'CredentialTypeRequest': {}}}}
        original = copy.deepcopy(result)

        filter_credential_type_schema(result, None, None, None)

        assert result == original

    def test_differentiates_required_vs_optional_fields(self):
        """Test that CredentialTypeRequest excludes None but PatchedCredentialTypeRequest includes it."""
        result = {
            'components': {
                'schemas': {
                    'CredentialTypeRequest': {'properties': {'kind': {'enum': ['ssh', 'vault', 'net', 'scm', 'cloud', 'registry', None]}}},
                    'PatchedCredentialTypeRequest': {'properties': {'kind': {'enum': ['ssh', 'vault', 'net', 'scm', 'cloud', 'registry', None]}}},
                }
            }
        }

        filter_credential_type_schema(result, None, None, None)

        # POST/PUT schema: no None (required field)
        assert result['components']['schemas']['CredentialTypeRequest']['properties']['kind']['enum'] == ['cloud', 'net']

        # PATCH schema: includes None (optional field)
        assert result['components']['schemas']['PatchedCredentialTypeRequest']['properties']['kind']['enum'] == ['cloud', 'net', None]


class TestInjectAiDescriptions:
    """Unit tests for inject_ai_descriptions postprocessing hook."""

    def _make_result(self, operations):
        """Build a minimal OpenAPI result dict from a list of (path, method, operationId, existing_desc) tuples."""
        paths = {}
        for path, method, op_id, desc in operations:
            paths.setdefault(path, {})[method] = {'operationId': op_id}
            if desc:
                paths[path][method]['x-ai-description'] = desc
        return {'paths': paths}

    def test_injects_missing_descriptions(self):
        """Test that descriptions are injected for operations without x-ai-description."""
        overlay = {'op_list': 'List items', 'op_create': 'Create an item'}
        result = self._make_result(
            [
                ('/api/v2/items/', 'get', 'op_list', None),
                ('/api/v2/items/', 'post', 'op_create', None),
            ]
        )

        with patch('builtins.open', mock_open(read_data=json.dumps(overlay))):
            returned = inject_ai_descriptions(result, None, None, None)

        assert result['paths']['/api/v2/items/']['get']['x-ai-description'] == 'List items'
        assert result['paths']['/api/v2/items/']['post']['x-ai-description'] == 'Create an item'
        assert returned is result

    def test_does_not_overwrite_existing_descriptions(self):
        """Test that existing x-ai-description from decorators is preserved."""
        overlay = {'op_list': 'Overlay description'}
        result = self._make_result(
            [
                ('/api/v2/items/', 'get', 'op_list', 'Decorator description'),
            ]
        )

        with patch('builtins.open', mock_open(read_data=json.dumps(overlay))):
            inject_ai_descriptions(result, None, None, None)

        assert result['paths']['/api/v2/items/']['get']['x-ai-description'] == 'Decorator description'

    def test_skips_operations_not_in_overlay(self):
        """Test that operations without a matching operationId in the overlay are unchanged."""
        overlay = {'op_other': 'Other description'}
        result = self._make_result(
            [
                ('/api/v2/items/', 'get', 'op_list', None),
            ]
        )

        with patch('builtins.open', mock_open(read_data=json.dumps(overlay))):
            inject_ai_descriptions(result, None, None, None)

        assert 'x-ai-description' not in result['paths']['/api/v2/items/']['get']

    def test_handles_missing_overlay_file(self):
        """Test graceful handling when the overlay file doesn't exist."""
        result = self._make_result(
            [
                ('/api/v2/items/', 'get', 'op_list', None),
            ]
        )
        original = copy.deepcopy(result)

        with patch('builtins.open', side_effect=FileNotFoundError):
            returned = inject_ai_descriptions(result, None, None, None)

        assert result == original
        assert returned is result

    def test_handles_invalid_json(self):
        """Test graceful handling when the overlay file contains invalid JSON."""
        result = self._make_result(
            [
                ('/api/v2/items/', 'get', 'op_list', None),
            ]
        )
        original = copy.deepcopy(result)

        with patch('builtins.open', mock_open(read_data='not valid json')):
            returned = inject_ai_descriptions(result, None, None, None)

        assert result == original
        assert returned is result

    def test_handles_empty_result(self):
        """Test graceful handling when result has no paths."""
        result = {}
        overlay = {'op_list': 'List items'}

        with patch('builtins.open', mock_open(read_data=json.dumps(overlay))):
            returned = inject_ai_descriptions(result, None, None, None)

        assert returned is result

    def test_skips_non_dict_path_items(self):
        """Test that non-dict values in path items (e.g. parameters list) are skipped."""
        overlay = {'op_list': 'List items'}
        result = {
            'paths': {
                '/api/v2/items/': {
                    'parameters': [{'name': 'id', 'in': 'path'}],
                    'get': {'operationId': 'op_list'},
                }
            }
        }

        with patch('builtins.open', mock_open(read_data=json.dumps(overlay))):
            inject_ai_descriptions(result, None, None, None)

        assert result['paths']['/api/v2/items/']['get']['x-ai-description'] == 'List items'

    def test_handles_operation_without_operation_id(self):
        """Test that operations without operationId are skipped."""
        overlay = {'op_list': 'List items'}
        result = {'paths': {'/api/v2/items/': {'get': {'summary': 'List'}}}}

        with patch('builtins.open', mock_open(read_data=json.dumps(overlay))):
            inject_ai_descriptions(result, None, None, None)

        assert 'x-ai-description' not in result['paths']['/api/v2/items/']['get']


class TestInjectCleanTextPatternComponents:
    """Unit tests for inject_clean_text_pattern_components postprocessing hook."""

    FIELD_ITEM_REF = {'$ref': '#/components/schemas/CleanTextNestedStringField'}
    TARGET_SCHEMAS = (
        'CredentialType',
        'CredentialTypeRequest',
        'PatchedCredentialTypeRequest',
    )
    ENHANCED_NOTE = (
        'When ENHANCED_INPUT_VALIDATION_ENABLED is on, non-secret string '
        'entries in fields[] may include optional pattern, patternDescription, '
        'and flags (Tier 2). Secret and non-string fields omit them. '
        'Requiredness is expressed via inputs.required, not per-field required.'
    )

    def _make_result(self, schemas=None):
        """Build a minimal OpenAPI result with optional CredentialType schemas."""
        if schemas is None:
            schemas = {name: {'properties': {'inputs': {'type': 'object'}}} for name in self.TARGET_SCHEMAS}
        return {'components': {'schemas': schemas}}

    def _assert_inputs_shape(self, inputs, *, expect_default=False, expect_note=True):
        assert inputs['type'] == 'object'
        assert inputs['additionalProperties'] is True
        assert inputs['properties']['fields'] == {
            'type': 'array',
            'description': 'Input field catalog. Dynamic per credential type.',
            'items': self.FIELD_ITEM_REF,
        }
        assert inputs['properties']['required'] == {
            'type': 'array',
            'items': {'type': 'string'},
            'description': 'Optional list of field ids that are required.',
        }
        assert inputs['properties']['metadata']['type'] == 'array'
        assert inputs['properties']['metadata']['items'] == self.FIELD_ITEM_REF
        if expect_note:
            assert self.ENHANCED_NOTE in inputs['description']
        if expect_default:
            assert 'default' in inputs
        else:
            assert 'default' not in inputs

    def test_injects_dab_components_and_shapes_credential_type_inputs(self):
        """Hook registers shared CleanText components and shapes CredentialType.inputs."""
        result = self._make_result()

        returned = inject_clean_text_pattern_components(result, None, None, None)

        schemas = result['components']['schemas']
        assert 'CleanTextNestedStringField' in schemas
        assert 'CleanTextFieldInfo' in schemas
        for name in self.TARGET_SCHEMAS:
            self._assert_inputs_shape(schemas[name]['properties']['inputs'])
        assert returned is result

    def test_preserves_existing_description_and_appends_note(self):
        """Existing inputs.description is kept and the enhanced-validation note is appended once."""
        existing = 'Custom inputs description.'
        result = self._make_result(
            {
                'CredentialType': {
                    'properties': {
                        'inputs': {
                            'type': 'object',
                            'description': existing,
                        }
                    }
                }
            }
        )

        inject_clean_text_pattern_components(result, None, None, None)

        description = result['components']['schemas']['CredentialType']['properties']['inputs']['description']
        assert description.startswith(existing)
        assert self.ENHANCED_NOTE in description
        assert description.count(self.ENHANCED_NOTE) == 1

    def test_does_not_duplicate_note_when_already_present(self):
        """Re-running the hook must not append the enhanced-validation note twice."""
        base = 'Enter inputs using either JSON or YAML syntax.'
        result = self._make_result(
            {
                'CredentialTypeRequest': {
                    'properties': {
                        'inputs': {
                            'type': 'object',
                            'description': f'{base} {self.ENHANCED_NOTE}',
                        }
                    }
                }
            }
        )

        inject_clean_text_pattern_components(result, None, None, None)

        description = result['components']['schemas']['CredentialTypeRequest']['properties']['inputs']['description']
        assert description.count(self.ENHANCED_NOTE) == 1

    def test_preserves_existing_default(self):
        """Existing inputs.default is preserved on the reshaped schema."""
        result = self._make_result(
            {
                'PatchedCredentialTypeRequest': {
                    'properties': {
                        'inputs': {
                            'type': 'object',
                            'default': {'fields': []},
                        }
                    }
                }
            }
        )

        inject_clean_text_pattern_components(result, None, None, None)

        inputs = result['components']['schemas']['PatchedCredentialTypeRequest']['properties']['inputs']
        self._assert_inputs_shape(inputs, expect_default=True)
        assert inputs['default'] == {'fields': []}

    def test_skips_missing_and_non_dict_schemas(self):
        """Missing or non-dict schemas are left alone; other schemas are untouched."""
        result = {
            'components': {
                'schemas': {
                    'CredentialType': 'not-a-dict',
                    'OtherSchema': {'properties': {'inputs': {'type': 'string'}}},
                }
            }
        }
        other_before = copy.deepcopy(result['components']['schemas']['OtherSchema'])

        inject_clean_text_pattern_components(result, None, None, None)

        assert result['components']['schemas']['CredentialType'] == 'not-a-dict'
        assert result['components']['schemas']['OtherSchema'] == other_before
        assert 'CredentialTypeRequest' not in result['components']['schemas']

    def test_handles_empty_result(self):
        """Empty result still gets shared CleanText components from DAB."""
        result = {}

        returned = inject_clean_text_pattern_components(result, None, None, None)

        assert 'CleanTextNestedStringField' in result['components']['schemas']
        assert returned is result

    def test_import_error_returns_result_unchanged(self):
        """When DAB shared schemas are unavailable, the hook is a no-op."""
        result = self._make_result()
        original = copy.deepcopy(result)

        with patch.dict(
            'sys.modules',
            {'ansible_base.api_documentation.clean_text_schema_hooks': None},
        ):
            returned = inject_clean_text_pattern_components(result, None, None, None)

        assert result == original
        assert returned is result
