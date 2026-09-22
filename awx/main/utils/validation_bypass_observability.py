"""Register django-ansible-base ORM bypass caller attribution for AWX."""

from ansible_base.lib.utils.validation_signals import (
    extend_caller_allowlist_prefixes,
    extend_internal_caller_prefixes,
    register_validation_signals,
)


def configure_validation_bypass_observability() -> None:
    """Call from AppConfig.ready() so ORM bypass logs show AWX entry points."""
    register_validation_signals()
    extend_caller_allowlist_prefixes(
        [
            "awx.api.views",
            "awx.api.serializers",
            "awx.main.tasks",
            "awx.main.management",
            "awx.main.utils",
        ]
    )
    extend_internal_caller_prefixes(
        [
            "awx.main.models",
            "awx.main.signals",
            "awx.main.dispatch",
        ]
    )
