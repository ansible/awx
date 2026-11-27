from django.utils.translation import gettext_lazy

from awx.main.tasks.policy import format_policy_results


def test_format_policy_results_keeps_long_messages_on_one_line():
    long_message = "Job Template name 'deploy prod' must start with the team prefix and contain only lowercase letters, digits and hyphens."

    details = format_policy_results({"Violations": {"Job template": [long_message]}})

    assert details == f"Violations:\n  Job template:\n    - {long_message}"


def test_format_policy_results_preserves_newlines_in_a_message():
    message = "Name is invalid.\nSee https://example.com/standards for the naming rules."

    details = format_policy_results({"Violations": {"Job template": [message]}})

    assert details == ("Violations:\n  Job template:\n    - Name is invalid.\n      See https://example.com/standards for the naming rules.")


def test_format_policy_results_renders_errors_and_violations_together():
    details = format_policy_results(
        {
            "Errors": {"Organization": "Call to OPA failed. Exception: Invalid JSON"},
            "Violations": {"Inventory": ["Access not allowed.", "Inventory must be scoped."]},
        }
    )

    assert details == (
        "Errors:\n"
        "  Organization: Call to OPA failed. Exception: Invalid JSON\n"
        "Violations:\n"
        "  Inventory:\n"
        "    - Access not allowed.\n"
        "    - Inventory must be scoped."
    )


def test_format_policy_results_does_not_quote_or_escape():
    message = "Name must not contain 'spaces'.\nUse hyphens instead."

    details = format_policy_results({"Violations": {"Job template": [message]}})

    assert "\\n" not in details
    assert '"' not in details
    assert details.count("'spaces'") == 1


def test_format_policy_results_handles_lazy_translated_messages():
    """Error messages are gettext_lazy proxies, not str.

    They are not str instances and iterate character by character, so a
    sequence check that tests for str instead of list would bullet every
    single letter of the message.
    """
    message = gettext_lazy('OPA policy returned invalid result.')

    details = format_policy_results({"Errors": {"Organization": message}})

    assert details == "Errors:\n  Organization: OPA policy returned invalid result."
