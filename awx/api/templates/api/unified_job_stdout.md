# Retrieve {{ model_verbose_name|title }} Stdout:

Make GET request to this resource to retrieve the stdout from running this
{{ model_verbose_name }}.

## Format

Use the `format` query string parameter to specify the output format.

* Browsable API: `?format=api`
* HTML: `?format=html`
* Plain Text: `?format=txt`
* Plain Text with ANSI color codes: `?format=ansi`
* JSON structure: `?format=json`

(_New in Ansible Tower 2.0.0_) When using the Browsable API, HTML and JSON
formats, the `start_line` and `end_line` query string parameters can be used
to specify a range of line numbers to retrieve.

Use `dark=1` or `dark=0` as a query string parameter to force or disable a
dark background.

{% include "api/_new_in_awx.md" %}
