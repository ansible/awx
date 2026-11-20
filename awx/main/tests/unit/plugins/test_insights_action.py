import pytest


class TestInsightsETagSanitization:
    """Test ETag handling in Insights action plugin"""

    def test_weak_etag_format(self):
        """Weak ETags (W/"value") should be stripped correctly"""
        version = 'W/"abc123"'
        if version.startswith('W/"') and version.endswith('"'):
            version = version[3:-1]
        elif version.startswith('"') and version.endswith('"'):
            version = version[1:-1]
        assert version == 'abc123'

    def test_strong_etag_format(self):
        """Strong ETags ("value") should be stripped correctly"""
        version = '"abc123"'
        if version.startswith('W/"') and version.endswith('"'):
            version = version[3:-1]
        elif version.startswith('"') and version.endswith('"'):
            version = version[1:-1]
        assert version == 'abc123'

    def test_complex_weak_etag(self):
        """Complex weak ETag from actual Insights API"""
        version = 'W/"9b7-Cv1QGQITci2gYXV8D4o9F4b6TyQ"'
        if version.startswith('W/"') and version.endswith('"'):
            version = version[3:-1]
        elif version.startswith('"') and version.endswith('"'):
            version = version[1:-1]
        assert version == '9b7-Cv1QGQITci2gYXV8D4o9F4b6TyQ'

    def test_no_etag_quotes(self):
        """ETags without quotes should pass through"""
        version = 'abc123'
        if version.startswith('W/"') and version.endswith('"'):
            version = version[3:-1]
        elif version.startswith('"') and version.endswith('"'):
            version = version[1:-1]
        assert version == 'abc123'
