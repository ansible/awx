# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved
import sys

from django.core.management.base import BaseCommand
from django.conf import settings
from awx.main.models import CredentialType, Credential, ExecutionEnvironment


class Command(BaseCommand):
    """Create default execution environments, intended for new installs"""

    help = """
    Creates or updates the execution environments set in settings.DEFAULT_EXECUTION_ENVIRONMENTS if they are not yet created.
    Optionally provide authentication details to create or update a container registry credential that will be set on all of these default execution environments.
    Note that settings.DEFAULT_EXECUTION_ENVIRONMENTS is and ordered list, the first in the list will be used for project updates and system jobs.
    """

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
            type=bool,
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
            registry_cred_inputs = {
                "host": options.get("registry_url"),
                "password": options.get("registry_password"),
                "username": options.get("registry_username"),
                "verify_ssl": options.get("verify_ssl"),
            }
            registry_cred_type = CredentialType.objects.filter(kind="registry")
            if not registry_cred_type.exists():
                sys.stderr.write("No registry credential type found")
                sys.exit(1)
            registry_cred, created = Credential.objects.get_or_create(
                name="Default Execution Environment Registry Credential",
                managed_by_tower=True,
                credential_type=registry_cred_type[0],
                defaults={"inputs": registry_cred_inputs},
            )
            if created:
                changed = True
                print("Default Execution Environment Credential registered.")
            elif registry_cred.inputs != registry_cred_inputs:
                registry_cred.inputs = registry_cred_inputs
                registry_cred.save()
                changed = True
                print("Default Execution Environment Credential updated.")

        for ee in reversed(settings.DEFAULT_EXECUTION_ENVIRONMENTS):
            _, created = ExecutionEnvironment.objects.update_or_create(
                name=ee["name"], defaults={"image": ee["image"], "managed_by_tower": True, "credential": registry_cred}
            )

        if created:
            changed = True
            print("Default Execution Environment(s) registered.")

        if changed:
            print("(changed: True)")
        else:
            print("(changed: False)")
