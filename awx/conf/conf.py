# Django
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

# Tower
from awx.conf import fields, register
from awx.conf import settings_registry

# Define a conf.py file within your app and register each setting similarly to
# the example below. Any field class from Django REST Framework or subclass
# thereof can be used for validation/conversion of the setting. All keyword
# arguments to the register function (except field_class, category,
# category_slug, depends_on, placeholder) will be used to initialize
# the field_class.

register(
    'ANSIBLE_COW_SELECTION',
    field_class=fields.ChoiceField,
    choices=[
        ('bud-frogs', _('Bud Frogs')),
        ('bunny', _('Bunny')),
        ('cheese', _('Cheese')),
        ('daemon', _('Daemon')),
        ('default', _('Default Cow')),
        ('dragon', _('Dragon')),
        ('elephant-in-snake', _('Elephant in Snake')),
        ('elephant', _('Elephant')),
        ('eyes', _('Eyes')),
        ('hellokitty', _('Hello Kitty')),
        ('kitty', _('Kitty')),
        ('luke-koala', _('Luke Koala')),
        ('meow', _('Meow')),
        ('milk', _('Milk')),
        ('moofasa', _('Moofasa')),
        ('moose', _('Moose')),
        ('ren', _('Ren')),
        ('sheep', _('Sheep')),
        ('small', _('Small Cow')),
        ('stegosaurus', _('Stegosaurus')),
        ('stimpy', _('Stimpy')),
        ('supermilker', _('Super Milker')),
        ('three-eyes', _('Three Eyes')),
        ('turkey', _('Turkey')),
        ('turtle', _('Turtle')),
        ('tux', _('Tux')),
        ('udder', _('Udder')),
        ('vader-koala', _('Vader Koala')),
        ('vader', _('Vader')),
        ('www', _('WWW')),
    ],
    default='default',
    label=_('Cow Selection'),
    help_text=_('Select which cow to use with cowsay when running jobs.'),
    category=_('Cows'),
    # Optional; category_slug will be slugified version of category if not
    # explicitly provided.
    category_slug='cows',
)


def _get_read_only_ansible_cow_selection_default():
    return getattr(settings, 'ANSIBLE_COW_SELECTION', 'No default cow!')


register(
    'READONLY_ANSIBLE_COW_SELECTION',
    field_class=fields.CharField,
    # read_only must be set via kwargs even if field_class sets it.
    read_only=True,
    # default can be a callable to dynamically compute the value; should be in
    # the plain JSON format stored in the DB and used in the API.
    default=_get_read_only_ansible_cow_selection_default,
    label=_('Example Read-Only Setting'),
    help_text=_('Example setting that cannot be changed.'),
    category=_('Cows'),
    category_slug='cows',
    # Optional; list of other settings this read-only setting depends on. When
    # the other settings change, the cached value for this setting will be
    # cleared to require it to be recomputed.
    depends_on=['ANSIBLE_COW_SELECTION'],
    # Optional; field is stored encrypted in the database and only $encrypted$
    # is returned via the API.
    encrypted=True,
)

register(
    'EXAMPLE_USER_SETTING',
    field_class=fields.CharField,
    allow_blank=True,
    label=_('Example Setting'),
    help_text=_('Example setting which can be different for each user.'),
    category=_('User'),
    category_slug='user',
    default='',
)

# Unregister the example settings above.
settings_registry.unregister('ANSIBLE_COW_SELECTION')
settings_registry.unregister('READONLY_ANSIBLE_COW_SELECTION')
settings_registry.unregister('EXAMPLE_USER_SETTING')
