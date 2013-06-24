from django.core.management.base import LabelCommand
from django.template import loader
from django.template import TemplateDoesNotExist
import sys


def get_template_path(path):
    try:
        template = loader.find_template(path)
        if template[1]:
            return template[1].name
        # work arround https://code.djangoproject.com/ticket/17199 issue
        for template_loader in loader.template_source_loaders:
            try:
                source, origin = template_loader.load_template_source(path)
                return origin
            except TemplateDoesNotExist:
                pass
        raise TemplateDoesNotExist(path)
    except TemplateDoesNotExist:
        return None


class Command(LabelCommand):
    help = "Finds the location of the given template by resolving its path"
    args = "[template_path]"
    label = 'template path'

    def handle_label(self, template_path, **options):
        path = get_template_path(template_path)
        if path is None:
            sys.stderr.write("No template found\n")
            sys.exit(1)
        else:
            print(path)
