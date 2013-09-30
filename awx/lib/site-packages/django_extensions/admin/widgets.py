import six
import django
from django import forms
from django.conf import settings
from django.contrib.admin.sites import site
from django.utils.safestring import mark_safe
if django.get_version() >= "1.4":
    from django.utils.text import Truncator
else:
    from django.utils.text import truncate_words
from django.template.loader import render_to_string
from django.contrib.admin.widgets import ForeignKeyRawIdWidget


class ForeignKeySearchInput(ForeignKeyRawIdWidget):
    """
    A Widget for displaying ForeignKeys in an autocomplete search input
    instead in a <select> box.
    """
    # Set in subclass to render the widget with a different template
    widget_template = None
    # Set this to the patch of the search view
    search_path = '../foreignkey_autocomplete/'

    def _media(self):
        js_files = ['django_extensions/js/jquery.bgiframe.min.js',
                    'django_extensions/js/jquery.ajaxQueue.js',
                    'django_extensions/js/jquery.autocomplete.js']
        if django.get_version() < "1.3":
            js_files.append('django_extensions/js/jquery.js')
        return forms.Media(css={'all': ('django_extensions/css/jquery.autocomplete.css',)},
                           js=js_files)

    media = property(_media)

    def label_for_value(self, value):
        key = self.rel.get_related_field().name
        obj = self.rel.to._default_manager.get(**{key: value})
        if django.get_version() >= "1.4":
            return Truncator(obj).words(14, truncate='...')
        else:
            return truncate_words(obj, 14)

    def __init__(self, rel, search_fields, attrs=None):
        self.search_fields = search_fields
        if django.get_version() >= "1.4":
            super(ForeignKeySearchInput, self).__init__(rel, site, attrs)
        else:
            super(ForeignKeySearchInput, self).__init__(rel, attrs)

    def render(self, name, value, attrs=None):
        if attrs is None:
            attrs = {}
        #output = [super(ForeignKeySearchInput, self).render(name, value, attrs)]
        opts = self.rel.to._meta
        app_label = opts.app_label
        model_name = opts.object_name.lower()
        related_url = '../../../%s/%s/' % (app_label, model_name)
        params = self.url_parameters()
        if params:
            url = '?' + '&amp;'.join(['%s=%s' % (k, v) for k, v in params.items()])
        else:
            url = ''
        if not 'class' in attrs:
            attrs['class'] = 'vForeignKeyRawIdAdminField'
        # Call the TextInput render method directly to have more control
        output = [forms.TextInput.render(self, name, value, attrs)]
        if value:
            label = self.label_for_value(value)
        else:
            label = six.u('')

        try:
            admin_media_prefix = settings.ADMIN_MEDIA_PREFIX
        except AttributeError:
            admin_media_prefix = settings.STATIC_URL + "admin/"

        context = {
            'url': url,
            'related_url': related_url,
            'admin_media_prefix': admin_media_prefix,
            'search_path': self.search_path,
            'search_fields': ','.join(self.search_fields),
            'model_name': model_name,
            'app_label': app_label,
            'label': label,
            'name': name,
            'pre_django_14': (django.VERSION[:2] < (1, 4)),
        }
        output.append(render_to_string(self.widget_template or (
            'django_extensions/widgets/%s/%s/foreignkey_searchinput.html' % (app_label, model_name),
            'django_extensions/widgets/%s/foreignkey_searchinput.html' % app_label,
            'django_extensions/widgets/foreignkey_searchinput.html',
        ), context))
        output.reverse()
        return mark_safe(six.u('').join(output))
