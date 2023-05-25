import tempfile
import tarfile
import stat
import os

from awx.main.models.inventory import CustomInventoryScript

from django.core.management.base import BaseCommand
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Export custom inventory scripts into a tarfile.'

    def add_arguments(self, parser):
        parser.add_argument('--filename', dest='filename', type=str, default='custom_scripts.tar', help='Filename of the output tar file')

    def handle(self, **options):
        tar_filename = options.get('filename')

        with tempfile.TemporaryDirectory() as tmpdirname:
            with tarfile.open(tar_filename, "w") as tar:
                for cis in CustomInventoryScript.objects.all():
                    # naming convention similar to project paths
                    slug_name = slugify(str(cis.name)).replace(u'-', u'_')
                    script_filename = u'_%d__%s' % (int(cis.pk), slug_name)
                    script_path = os.path.join(tmpdirname, script_filename)

                    with open(script_path, 'w') as f:
                        f.write(cis.script)
                    os.chmod(script_path, stat.S_IRWXU)
                    tar.add(script_path, arcname=script_filename)

        print('Dump of old custom inventory scripts at {}'.format(tar_filename))
