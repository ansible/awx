from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext as _
from django.utils import six

from taggit.utils import parse_tags, edit_string_for_tags


class TagWidget(forms.TextInput):
    def render(self, name, value, attrs=None):
        if value is not None and not isinstance(value, six.string_types):
            value = edit_string_for_tags([o.tag for o in value.select_related("tag")])
        return super(TagWidget, self).render(name, value, attrs)

class TagField(forms.CharField):
    widget = TagWidget

    def clean(self, value):
        value = super(TagField, self).clean(value)
        try:
            return parse_tags(value)
        except ValueError:
            raise forms.ValidationError(_("Please provide a comma-separated list of tags."))
