import os
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.core.management.color import color_style
from django.template.base import add_to_builtins
from django.template.loaders.filesystem import Loader
from django_extensions.utils import validatingtemplatetags

#
# TODO: Render the template with fake request object ?
#


class Command(BaseCommand):
    args = ''
    help = "Validate templates on syntax and compile errors"
    option_list = BaseCommand.option_list + (
        make_option('--break', '-b', action='store_true', dest='break',
                    default=False, help="Break on first error."),
        make_option('--check-urls', '-u', action='store_true', dest='check_urls',
                    default=False, help="Check url tag view names are quoted appropriately"),
        make_option('--force-new-urls', '-n', action='store_true', dest='force_new_urls',
                    default=False, help="Error on usage of old style url tags (without {% load urls from future %}"),
        make_option('--include', '-i', action='append', dest='includes',
                    default=[], help="Append these paths to TEMPLATE_DIRS")
    )

    def handle(self, *args, **options):
        from django.conf import settings
        style = color_style()
        template_dirs = set(settings.TEMPLATE_DIRS)
        template_dirs |= set(options.get('includes', []))
        template_dirs |= set(getattr(settings, 'VALIDATE_TEMPLATES_EXTRA_TEMPLATE_DIRS', []))
        settings.TEMPLATE_DIRS = list(template_dirs)
        settings.TEMPLATE_DEBUG = True
        verbosity = int(options.get('verbosity', 1))
        errors = 0

        template_loader = Loader()

        # Replace built in template tags with our own validating versions
        if options.get('check_urls', False):
            add_to_builtins('django_extensions.utils.validatingtemplatetags')

        for template_dir in template_dirs:
            for root, dirs, filenames in os.walk(template_dir):
                for filename in filenames:
                    if filename.endswith(".swp"):
                        continue
                    if filename.endswith("~"):
                        continue
                    filepath = os.path.join(root, filename)
                    if verbosity > 1:
                        print(filepath)
                    validatingtemplatetags.before_new_template(options.get('force_new_urls', False))
                    try:
                        template_loader.load_template(filename, [root])
                    except Exception as e:
                        errors += 1
                        print("%s: %s" % (filepath, style.ERROR("%s %s" % (e.__class__.__name__, str(e)))))
                    template_errors = validatingtemplatetags.get_template_errors()
                    for origin, line, message in template_errors:
                        errors += 1
                        print("%s(%s): %s" % (origin, line, style.ERROR(message)))
                    if errors and options.get('break', False):
                        raise CommandError("Errors found")

        if errors:
            raise CommandError("%s errors found" % errors)
        print("%s errors found" % errors)

