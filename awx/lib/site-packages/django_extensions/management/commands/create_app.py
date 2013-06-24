import os
import re
import sys
import django_extensions
from django.conf import settings
from django.db import connection
from django.core.management.base import CommandError, LabelCommand
from django.template import Template, Context
from django_extensions.settings import REPLACEMENTS
from django_extensions.utils.dia2django import dia2django
from django_extensions.management.utils import _make_writeable
from optparse import make_option


class Command(LabelCommand):
    option_list = LabelCommand.option_list + (
        make_option('--template', '-t', action='store', dest='app_template',
                    help='The path to the app template'),
        make_option('--parent_path', '-p', action='store', dest='parent_path',
                    help='The parent path of the application to be created'),
        make_option('-d', action='store_true', dest='dia_parse',
                    help='Generate model.py and admin.py from [APP_NAME].dia file'),
        make_option('--diagram', action='store', dest='dia_path',
                    help='The diagram path of the app to be created. -d is implied'),
    )

    help = ("Creates an application directory structure for the specified application name.")
    args = "APP_NAME"
    label = 'application name'

    requires_model_validation = False
    can_import_settings = True

    def handle_label(self, label, **options):
        project_dir = os.getcwd()
        project_name = os.path.split(project_dir)[-1]
        app_name = label
        app_template = options.get('app_template') or os.path.join(django_extensions.__path__[0], 'conf', 'app_template')
        app_dir = os.path.join(options.get('parent_path') or project_dir, app_name)
        dia_path = options.get('dia_path') or os.path.join(project_dir, '%s.dia' % app_name)

        if not os.path.exists(app_template):
            raise CommandError("The template path, %r, does not exist." % app_template)

        if not re.search(r'^\w+$', label):
            raise CommandError("%r is not a valid application name. Please use only numbers, letters and underscores." % label)

        dia_parse = options.get('dia_path') or options.get('dia_parse')
        if dia_parse:
            if not os.path.exists(dia_path):
                raise CommandError("The diagram path, %r, does not exist." % dia_path)
            if app_name in settings.INSTALLED_APPS:
                raise CommandError("The application %s should not be defined in the settings file. Please remove %s now, and add it after using this command." % (app_name, app_name))
            tables = [name for name in connection.introspection.table_names() if name.startswith('%s_' % app_name)]
            if tables:
                raise CommandError("%r application has tables in the database. Please delete them." % app_name)

        try:
            os.makedirs(app_dir)
        except OSError as e:
            raise CommandError(e)

        copy_template(app_template, app_dir, project_name, app_name)

        if dia_parse:
            generate_models_and_admin(dia_path, app_dir, project_name, app_name)
            print("Application %r created." % app_name)
            print("Please add now %r and any other dependent application in settings.INSTALLED_APPS, and run 'manage syncdb'" % app_name)


def copy_template(app_template, copy_to, project_name, app_name):
    """copies the specified template directory to the copy_to location"""
    import shutil

    app_template = os.path.normpath(app_template)
    # walks the template structure and copies it
    for d, subdirs, files in os.walk(app_template):
        relative_dir = d[len(app_template) + 1:]
        d_new = os.path.join(copy_to, relative_dir).replace('app_name', app_name)
        if relative_dir and not os.path.exists(d_new):
            os.mkdir(d_new)
        for i, subdir in enumerate(subdirs):
            if subdir.startswith('.'):
                del subdirs[i]
        replacements = {'app_name': app_name, 'project_name': project_name}
        replacements.update(REPLACEMENTS)
        for f in files:
            if f.endswith('.pyc') or f.startswith('.DS_Store'):
                continue
            path_old = os.path.join(d, f)
            path_new = os.path.join(d_new, f.replace('app_name', app_name))
            if os.path.exists(path_new):
                path_new = os.path.join(d_new, f)
                if os.path.exists(path_new):
                    continue
            if path_new.endswith('.tmpl'):
                path_new = path_new[:-5]
            fp_old = open(path_old, 'r')
            fp_new = open(path_new, 'w')
            fp_new.write(Template(fp_old.read()).render(Context(replacements)))
            fp_old.close()
            fp_new.close()
            try:
                shutil.copymode(path_old, path_new)
                _make_writeable(path_new)
            except OSError:
                sys.stderr.write("Notice: Couldn't set permission bits on %s. You're probably using an uncommon filesystem setup. No problem.\n" % path_new)


def generate_models_and_admin(dia_path, app_dir, project_name, app_name):
    """Generates the models.py and admin.py files"""

    def format_text(string, indent=False):
        """format string in lines of 80 or less characters"""
        retval = ''
        while string:
            line = string[:77]
            last_space = line.rfind(' ')
            if last_space != -1 and len(string) > 77:
                retval += "%s \\\n" % string[:last_space]
                string = string[last_space + 1:]
            else:
                retval += "%s\n" % string
                string = ''
            if string and indent:
                string = '    %s' % string
        return retval

    model_path = os.path.join(app_dir, 'models.py')
    admin_path = os.path.join(app_dir, 'admin.py')

    models_txt = 'from django.db import models\n' + dia2django(dia_path)
    open(model_path, 'w').write(models_txt)

    classes = re.findall('class (\w+)', models_txt)
    admin_txt = 'from django.contrib.admin import site, ModelAdmin\n' + format_text('from %s.%s.models import %s' % (project_name, app_name, ', '.join(classes)), indent=True)
    admin_txt += format_text('\n\n%s' % '\n'.join(map((lambda t: 'site.register(%s)' % t), classes)))
    open(admin_path, 'w').write(admin_txt)
