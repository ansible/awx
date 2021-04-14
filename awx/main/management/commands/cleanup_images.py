# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import subprocess
import logging
import json

# Django
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

# AWX
from awx.main.models import ExecutionEnvironment


class Command(BaseCommand):
    """
    Management command to cleanup unused execution environment images.
    """

    help = 'Remove unused execution environment images'

    def init_logging(self):
        log_levels = dict(enumerate([logging.ERROR, logging.INFO, logging.DEBUG, 0]))
        self.logger = logging.getLogger('awx.main.commands.cleanup_images')
        self.logger.setLevel(log_levels.get(self.verbosity, 0))
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)
        self.logger.propagate = False

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', dest='dry_run', action='store_true', default=False, help='Dry run mode (show items that would ' 'be removed)')

    def delete_images(self, images_json):
        if self.dry_run:
            delete_prefix = "Would delete"
        else:
            delete_prefix = "Deleting"
        for e in images_json:
            if 'Names' in e:
                image_names = e['Names']
            else:
                image_names = [e["Id"]]
            image_size = e['Size'] / 1e6
            for i in image_names:
                if i not in self.images_in_use and i not in self.deleted:
                    self.deleted.append(i)
                    self.logger.info(f"{delete_prefix} {i}: {image_size:.0f} MB")
                    if not self.dry_run:
                        subprocess.run(['podman', 'rmi', i, '-f'], stdout=subprocess.DEVNULL)

    def cleanup_images(self):
        self.images_in_use = [ee.image for ee in ExecutionEnvironment.objects.all()]
        if self.images_in_use:
            self.logger.info("Execution environment images in use:")
            for i in self.images_in_use:
                self.logger.info(f"\t{i}")
        self.deleted = []
        # find and remove unused images
        images_system = subprocess.run("podman images -a --format json".split(" "), capture_output=True)
        if len(images_system.stdout) > 0:
            images_system = json.loads(images_system.stdout)

            self.delete_images(images_system)
        # find and remove dangling images
        images_system = subprocess.run('podman images -a --filter "dangling=true" --format json'.split(" "), capture_output=True)
        if len(images_system.stdout) > 0:
            images_system = json.loads(images_system.stdout)
            self.delete_images(images_system)
        if not self.deleted:
            self.logger.info("Did not find unused images to remove")

    def handle(self, *args, **options):
        self.verbosity = int(options.get('verbosity', 1))
        self.init_logging()
        self.dry_run = bool(options.get('dry_run', False))
        if self.dry_run:
            self.logger.info("Dry run enabled, images will not be deleted")
        if settings.IS_K8S:
            raise CommandError("Cannot run cleanup tool on k8s installations")
        self.cleanup_images()
