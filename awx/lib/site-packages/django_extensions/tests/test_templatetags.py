from django.test import TestCase

from django_extensions.templatetags.widont import widont, widont_html


class TemplateTagsTests(TestCase):
    def test_widont(self):
        widont('Test Value')
        widont(u'Test Value')

    def test_widont_html(self):
        widont_html('Test Value')
        widont_html(u'Test Value')
