# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved
import sys
from distutils.util import strtobool
from argparse import RawTextHelpFormatter

from django.core.management.base import BaseCommand
from django.conf import settings
from awx.main.models import CredentialType, Credential, ExecutionEnvironment


class Command(BaseCommand):
    """Create default execution environments, intended for new installs"""

    help = """
    Creates or updates the execution environments set in settings.DEFAULT_EXECUTION_ENVIRONMENTS if they are not yet created.
    Optionally provide authentication details to create or update a container registry credential that will be set on all of these default execution environments.
    Note that settings.DEFAULT_EXECUTION_ENVIRONMENTS is and ordered list, the first in the list will be used for project updates.
    """

    # Preserves newlines in the help text
    def create_parser(self, *args, **kwargs):
        parser = super(Command, self).create_parser(*args, **kwargs)
        parser.formatter_class = RawTextHelpFormatter
        return parser

    def add_arguments(self, parser):
        parser.add_argument(
            "--registry-url",
            type=str,
            default="",
            help="URL for the container registry",
        )
        parser.add_argument(
            "--registry-username",
            type=str,
            default="",
            help="username for the container registry",
        )
        parser.add_argument(
            "--registry-password",
            type=str,
            default="",
            help="Password or token for CLI authentication with the container registry",
        )
        parser.add_argument(
            "--verify-ssl",
            type=lambda x: bool(strtobool(str(x))),
            default=True,
            help="Verify SSL when authenticating with the container registry",
        )

    def handle(self, *args, **options):
        changed = False
        registry_cred = None

        if options.get("registry_username"):
            if not options.get("registry_password"):
                sys.stderr.write("Registry password must be provided when providing registry username\n")
                sys.exit(1)

            if not options.get("registry_url"):
                sys.stderr.write("Registry url must be provided when providing registry username\n")
                sys.exit(1)

            registry_cred_type = CredentialType.objects.filter(kind="registry")
            if not registry_cred_type.exists():
                sys.stderr.write("No registry credential type found")
                sys.exit(1)

            inputs = {
                "host": options.get("registry_url"),
                "password": options.get("registry_password"),
                "username": options.get("registry_username"),
                "verify_ssl": options.get("verify_ssl"),
            }
            registry_cred, cred_created = Credential.objects.get_or_create(
                name="Default Execution Environment Registry Credential",
                managed=True,
                credential_type=registry_cred_type[0],
                defaults={'inputs': inputs},
            )

            if cred_created:
                changed = True
                print("'Default Execution Environment Credential' registered.")

            for key, value in inputs.items():
                if not registry_cred.inputs.get(key) or registry_cred.get_input(key) != value:
                    registry_cred.inputs[key] = value
                    changed = True

            if changed:
                registry_cred.save()
                print("'Default Execution Environment Credential' updated.")

        # Create default globally available Execution Environments
        for ee in reversed(settings.GLOBAL_JOB_EXECUTION_ENVIRONMENTS):
            _this_ee, ee_created = ExecutionEnvironment.objects.get_or_create(name=ee["name"], defaults={'image': ee["image"], 'credential': registry_cred})
            if ee_created:
                changed = True
                print(f"'{ee['name']}' Default Execution Environment registered.")
            else:
                if _this_ee.image != ee["image"]:
                    _this_ee.image = ee["image"]
                    changed = True
                if _this_ee.credential != registry_cred:
                    _this_ee.credential = registry_cred
                    changed = True
            if changed:
                _this_ee.save()
                print(f"'{ee['name']}' Default Execution Environment updated.")

        # Create the control plane execution environment that is used for project updates and system jobs
        ee = settings.CONTROL_PLANE_EXECUTION_ENVIRONMENT
        _this_ee, cp_created = ExecutionEnvironment.objects.get_or_create(
            name="Control Plane Execution Environment", defaults={'image': ee, 'managed': True, 'credential': registry_cred}
        )
        if cp_created:
            changed = True
            print("Control Plane Execution Environment registered.")
        else:
            if _this_ee.image != ee:
                _this_ee.image = ee
                changed = True
            if _this_ee.credential != registry_cred:
                _this_ee.credential = registry_cred
                changed = True
        if changed:
            _this_ee.save()

        if changed:
            print("(changed: True)")
        else:
            print("(changed: False)")
