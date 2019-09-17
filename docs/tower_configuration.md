Tower configuration gives Tower users the ability to adjust multiple runtime parameters of Tower, which enables much more fine-grained control over Tower runs.

## Usage manual

#### To Use:
The REST endpoint for CRUD operations against Tower configurations can be found at `/api/v2/settings/`. GETing to that endpoint will return a list of available Tower configuration categories and their URLs, such as `"system": "/api/v2/settings/system/"`. The URL given to each category is the endpoint for CRUD operations against individual settings under that category.

Here is a typical Tower configuration category GET response:
```
GET /api/v2/settings/github-team/
HTTP 200 OK
Allow: GET, PUT, PATCH, DELETE, HEAD, OPTIONS
Content-Type: application/json
Vary: Accept
X-API-Node: tower
X-API-Query-Count: 6
X-API-Query-Time: 0.004s
X-API-Time: 0.026s

{
    "SOCIAL_AUTH_GITHUB_TEAM_CALLBACK_URL": "https://towerhost/sso/complete/github-team/",
    "SOCIAL_AUTH_GITHUB_TEAM_KEY": "",
    "SOCIAL_AUTH_GITHUB_TEAM_SECRET": "",
    "SOCIAL_AUTH_GITHUB_TEAM_ID": "",
    "SOCIAL_AUTH_GITHUB_TEAM_ORGANIZATION_MAP": null,
    "SOCIAL_AUTH_GITHUB_TEAM_TEAM_MAP": null
}
```

The returned body is a JSON of key-value pairs, where the key is the name of the Tower configuration setting, and the value is the value of that setting. To update the settings, simply update setting values and PUT/PATCH to the same endpoint.

#### To Develop:
Each Django app in Tower should have a `conf.py` file where related settings get registered. Below is the general format for `conf.py`:

```python
# Other dependencies
# ...

# Django
from django.utils.translation import ugettext_lazy as _

# Tower
from awx.conf import fields, register

# Other dependencies
# ...

register(
  '<setting name>',
  ...
)
# Other setting registries
```

`register` is the endpoint API for registering individual Tower configurations:
```
register(
    setting,
    field_class=None,
    **field_related_kwargs,
    category_slug=None,
    category=None,
    depends_on=None,
    placeholder=rest_framework.fields.empty,
    encrypted=False,
    defined_in_file=False,
)
```
Here are the details for each argument:

| Argument Name               | Argument Value Type                                                  | Description                                                                                                                                                                   |
|--------------------------|-------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `setting`                | `str`                                                             | Name of the setting. Usually all-capital connected by underscores like `'FOO_BAR'`                                                                                            |
| `field_class`            | a subclass of DRF serializer field available in `awx.conf.fields` | The class wrapping around value of the configuration, responsible for retrieving, setting, validating and storing configuration values.                                       |
| `**field_related_kwargs` | `**kwargs`                                                          | Key-worded arguments needed to initialize an instance of `field_class`.                                                                                                       |
| `category_slug`          | `str`                                                             | The actual identifier used for finding individual setting categories.                                                                                                         |
| `category`               | transformable string, like `_('foobar')`                          | The human-readable form of `category_slug`, mainly for display.                                                                                                               |
| `depends_on`             | `list` of `str`s                                                  | A list of setting names this setting depends on. A setting this setting depends on is another Tower configuration setting whose changes may affect the value of this setting. |
| `placeholder`            | transformable string, like `_('foobar')`                          | A human-readable string displaying a typical value for the setting, mainly used by the UI.                                                                                         |
| `encrypted`              | `boolean`                                                         | A flag which determines whether the setting value should be encrypted.                                                                                                                |
| `defined_in_file`        | `boolean`                                                         | A flag which determines whether a value has been manually set in the settings file.                                                                                                      |

During Tower bootstrapping, **all** settings registered in `conf.py` modules of Tower Django apps will be loaded (registered). This set of Tower configuration settings will form a new top-level of the `django.conf.settings` object. Later, all Tower configuration settings will be available as attributes of it, just like the normal Django settings. Note that Tower configuration settings take higher priority over normal settings, meaning if a setting `FOOBAR` is both defined in a settings file *and* registered in `conf.py`, the registered attribute will be used over the defined attribute every time.

Please note that when registering new configurations, it is recommended to provide a default value if it is possible to do so, as the Tower configuration UI has a 'revert all' functionality that reverts all settings to its default value.

Starting with version 3.2, Tower configuration supports category-specific validation functions. They should also be defined under `conf.py` in the form
```python
def custom_validate(serializer, attrs):
    '''
    Method details
    '''
```
...where the argument `serializer` refers to the underlying `SettingSingletonSerializer` object, and `attrs` refers to a dictionary of input items.

At the end of `conf.py`, register defined custom validation methods to different configuration categories (`category_slug`) using `awx.conf.register_validate`:
```python
# conf.py
...
from awx.conf import register_validate
...
def validate_a(serializer, attrs):
...
def validate_b(serializer, attrs):
...
# At the end of conf.py
register_validate("category_a", validate_a)
register_validate("category_b", validate_b)
...
```

It should be noted that each validation function will be invoked in two places: when updating the category it's responsible for and when updating the general category `all`. Always keep this fact in mind and test both situations when developing new validation functions.
