from django.core.management.base import NoArgsCommand
from django_extensions.management.utils import get_project_root
from optparse import make_option
from os.path import join as _j
import os


class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--optimize', '-o', '-O', action='store_true', dest='optimize',
                    help='Remove optimized python bytecode files'),
        make_option('--path', '-p', action='store', dest='path',
                    help='Specify path to recurse into'),
    )
    help = "Removes all python bytecode compiled files from the project."

    requires_model_validation = False

    def handle_noargs(self, **options):
        project_root = options.get("path", None)
        if not project_root:
            project_root = get_project_root()
        exts = options.get("optimize", False) and [".pyc", ".pyo"] or [".pyc"]
        verbose = int(options.get("verbosity", 1))

        if verbose > 1:
            print("Project Root: %s" % project_root)

        for root, dirs, files in os.walk(project_root):
            for file in files:
                ext = os.path.splitext(file)[1]
                if ext in exts:
                    full_path = _j(root, file)
                    if verbose > 1:
                        print(full_path)
                    os.remove(full_path)

# Backwards compatibility for Django r9110
if not [opt for opt in Command.option_list if opt.dest == 'verbosity']:
    Command.option_list += (
        make_option('--verbosity', '-v', action="store", dest="verbosity",
                    default='1', type='choice', choices=['0', '1', '2'],
                    help="Verbosity level; 0=minimal output, 1=normal output, 2=all output"),
    )
