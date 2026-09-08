# Copyright (c) 2026 Ansible, Inc.
# All Rights Reserved.

from rest_framework import serializers

from awx.api import metadata as awx_metadata


class PlainSerializer(serializers.Serializer):
    name = serializers.CharField()


class TestMetadataGetFieldInfoInjectsTopLevelPatterns:
    def test_calls_inject_top_level_clean_text_patterns(self, monkeypatch):
        calls = []

        def fake_inject(field, field_info):
            calls.append((field, field_info))
            field_info['pattern'] = 'FAKE'
            return field_info

        monkeypatch.setattr(awx_metadata, 'inject_top_level_clean_text_patterns', fake_inject)

        serializer = PlainSerializer()
        field = serializer.fields['name']

        field_info = awx_metadata.Metadata().get_field_info(field)

        assert field_info['pattern'] == 'FAKE'
        assert len(calls) == 1
        assert calls[0][0] is field

    def test_no_op_when_dab_helper_missing(self, monkeypatch):
        # inject_top_level_clean_text_patterns itself no-ops when the DAB helper
        # is unavailable; verify Metadata still returns clean field_info in that case.
        monkeypatch.setattr(awx_metadata, 'inject_top_level_clean_text_patterns', lambda field, field_info: field_info)

        serializer = PlainSerializer()
        field = serializer.fields['name']

        field_info = awx_metadata.Metadata().get_field_info(field)

        assert 'pattern' not in field_info
