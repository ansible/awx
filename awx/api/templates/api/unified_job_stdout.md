# Retrieve {{ model_verbose_name|title }} Stdout:

Make GET request to this resource to retrieve the stdout from running this
{{ model_verbose_name }}.

## Format

Use the `format` query string parameter to specify the output format.

* Browsable API: `?format=api`
* HTML: `?format=html`
* Plain Text: `?format=txt`
* Plain Text with ANSI color codes: `?format=ansi`

When using the HTML or API formats, use the `scheme` query string parameter to
change the output colors.  The value must be one of the following (default is
`ansi2html`):

* `ansi2html`
* `osx`
* `xterm`
* `xterm-bright`
* `solarized`

Use `dark=1` or `dark=0` as a query string parameter to force or disable a
dark background.

{% include "api/_new_in_awx.md" %}
