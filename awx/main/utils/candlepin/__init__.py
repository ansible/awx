"""
Candlepin integration for mTLS-based authentication.

This package provides Candlepin consumer identity certificate support,
enabling AAP controller instances to authenticate analytics uploads using
mTLS instead of service account credentials.
"""

from .lifecycle import check_certificate_health, get_certificate_info

__all__ = ['check_certificate_health', 'get_certificate_info']
