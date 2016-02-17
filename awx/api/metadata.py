# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

# Django
from django.core.exceptions import PermissionDenied
from django.http import Http404

# Django REST Framework
from rest_framework import exceptions
from rest_framework import metadata
from rest_framework import serializers
from rest_framework.request import clone_request

# Ansible Tower
from awx.main.models import InventorySource, Notifier


class Metadata(metadata.SimpleMetadata):

    def get_field_info(self, field):
        field_info = super(Metadata, self).get_field_info(field)

        # Indicate if a field has a default value.
        # FIXME: Still isn't showing all default values?
        try:
            field_info['default'] = field.get_default()
        except serializers.SkipField:
            pass

        # Indicate if a field is write-only.
        if getattr(field, 'write_only', False):
            field_info['write_only'] = True

        # Update choices to be a list of 2-tuples instead of list of dicts with
        # value/display_name.
        if 'choices' in field_info:
            choices = []
            for choice in field_info['choices']:
                if isinstance(choice, dict):
                    choices.append((choice.get('value'), choice.get('display_name')))
                else:
                    choices.append(choice)
            field_info['choices'] = choices

        # Special handling of inventory source_region choices that vary based on
        # selected inventory source.
        if field.field_name == 'source_regions':
            for cp in ('azure', 'ec2', 'gce', 'rax'):
                get_regions = getattr(InventorySource, 'get_%s_region_choices' % cp)
                field_info['%s_region_choices' % cp] = get_regions()

        # Special handling of group_by choices for EC2.
        if field.field_name == 'group_by':
            for cp in ('ec2',):
                get_group_by_choices = getattr(InventorySource, 'get_%s_group_by_choices' % cp)
                field_info['%s_group_by_choices' % cp] = get_group_by_choices()

        # Special handling of notification configuration where the required properties
        # are conditional on the type selected.
        if field.field_name == 'notification_configuration':
            for (notification_type_name, notification_tr_name, notification_type_class) in Notifier.NOTIFICATION_TYPES:
                field_info[notification_type_name] = notification_type_class.init_parameters

        # Update type of fields returned...
        if field.field_name == 'type':
            field_info['type'] = 'multiple choice'
        elif field.field_name == 'url':
            field_info['type'] = 'string'
        elif field.field_name in ('related', 'summary_fields'):
            field_info['type'] = 'object'
        elif field.field_name in ('created', 'modified'):
            field_info['type'] = 'datetime'

        return field_info

    def determine_actions(self, request, view):
        # Add field information for GET requests (so field names/labels are
        # available even when we can't POST/PUT).
        actions = {}
        for method in {'GET', 'PUT', 'POST'} & set(view.allowed_methods):
            view.request = clone_request(request, method)
            try:
                # Test global permissions
                if hasattr(view, 'check_permissions'):
                    view.check_permissions(view.request)
                # Test object permissions
                if method == 'PUT' and hasattr(view, 'get_object'):
                    view.get_object()
            except (exceptions.APIException, PermissionDenied, Http404):
                continue
            else:
                # If user has appropriate permissions for the view, include
                # appropriate metadata about the fields that should be supplied.
                serializer = view.get_serializer()
                actions[method] = self.get_serializer_info(serializer)
            finally:
                view.request = request

            for field, meta in actions[method].items():
                if not isinstance(meta, dict):
                    continue

                # Add type choices if available from the serializer.
                if field == 'type' and hasattr(serializer, 'get_type_choices'):
                    meta['choices'] = serializer.get_type_choices()

                # For GET method, remove meta attributes that aren't relevant
                # when reading a field and remove write-only fields.
                if method == 'GET':
                    meta.pop('required', None)
                    meta.pop('read_only', None)
                    meta.pop('default', None)
                    meta.pop('min_length', None)
                    meta.pop('max_length', None)
                    if meta.pop('write_only', False):
                        actions['GET'].pop(field)

                # For PUT/POST methods, remove read-only fields.
                if method in ('PUT', 'POST'):
                    if meta.pop('read_only', False):
                        actions[method].pop(field)

        return actions

    def determine_metadata(self, request, view):
        metadata = super(Metadata, self).determine_metadata(request, view)

        # Add version number in which view was added to Tower.
        added_in_version = '1.2'
        for version in ('3.0.0', '2.4.0', '2.3.0', '2.2.0', '2.1.0', '2.0.0', '1.4.8', '1.4.5', '1.4', '1.3'):
            if getattr(view, 'new_in_%s' % version.replace('.', ''), False):
                added_in_version = version
                break
        metadata['added_in_version'] = added_in_version

        # Add type(s) handled by this view/serializer.
        serializer = view.get_serializer()
        if hasattr(serializer, 'get_types'):
            metadata['types'] = serializer.get_types()

        # Add search fields if available from the view.
        if getattr(view, 'search_fields', None):
            metadata['search_fields'] = view.search_fields

        return metadata
