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
* Downloaded Plain Text: `?format=txt_download`

(_New in Ansible Tower 2.0.0_) When using the Browsable API, HTML and JSON
formats, the `start_line` and `end_line` query string parameters can be used
to specify a range of line numbers to retrieve.

Use `dark=1` or `dark=0` as a query string parameter to force or disable a
dark background.

+Files over {{ settings.STDOUT_MAX_BYTES_DISPLAY|filesizeformat }} (configurable) will not display in the browser. Use the `txt_download`
+format to download the file directly to view it.

{% include "api/_new_in_awx.md" %}
