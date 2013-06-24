from django.core.management.base import NoArgsCommand
from django_extensions.management.utils import get_project_root
from optparse import make_option
from os.path import join as _j
import py_compile
import os


class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--path', '-p', action='store', dest='path', help='Specify path to recurse into'),
    )
    help = "Compile python bytecode files for the project."

    requires_model_validation = False

    def handle_noargs(self, **options):
        project_root = options.get("path", None)
        if not project_root:
            project_root = get_project_root()
        verbose = int(options.get("verbosity", 1)) > 1

        for root, dirs, files in os.walk(project_root):
            for file in files:
                ext = os.path.splitext(file)[1]
                if ext == ".py":
                    full_path = _j(root, file)
                    if verbose:
                        print("%sc" % full_path)
                    py_compile.compile(full_path)

# Backwards compatibility for Django r9110
if not [opt for opt in Command.option_list if opt.dest == 'verbosity']:
    Command.option_list += (
        make_option('--verbosity', '-v', action="store", dest="verbosity",
                    default='1', type='choice', choices=['0', '1', '2'],
                    help="Verbosity level; 0=minimal output, 1=normal output, 2=all output"),
    )
