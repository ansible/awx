import json
import os
import sys

from typing import Any
from django.core.management.base import BaseCommand
from django.conf import settings
from awx.conf import settings_registry


class Command(BaseCommand):
    help = 'Dump the current auth configuration in django_ansible_base.authenticator format, currently support LDAP'

    DAB_SAML_AUTHENTICATOR_KEYS = [
        "SP_ENTITY_ID",
        "SP_PUBLIC_CERT",
        "SP_PRIVATE_KEY",
        "ORG_INFO",
        "TECHNICAL_CONTACT",
        "SUPPORT_CONTACT",
        "SP_EXTRA",
        "SECURITY_CONFIG",
        "EXTRA_DATA",
        "ENABLED_IDPS",
        "CALLBACK_URL",
    ]

    def get_awx_saml_settings(self) -> tuple[bool, dict[str, Any]]:
        # settings_registry.get_registered_settings(category_slug='saml', read_only=False)
        awx_saml_settings = {}
        for awx_saml_setting in settings_registry.get_registered_settings(category_slug='saml'):
            # strip the prefix 'SOCIAL_AUTH_SAML_' from awx_saml_setting
            awx_saml_settings[awx_saml_setting.removeprefix("SOCIAL_AUTH_SAML_")] = getattr(settings, awx_saml_setting, None)

        is_enabled = all(
            [
                getattr(settings, "SOCIAL_AUTH_SAML_SP_ENTITY_ID", None),
                getattr(settings, "SOCIAL_AUTH_SAML_SP_PUBLIC_CERT", None),
                getattr(settings, "SOCIAL_AUTH_SAML_SP_PRIVATE_KEY", None),
                getattr(settings, "SOCIAL_AUTH_SAML_ORG_INFO", None),
                getattr(settings, "SOCIAL_AUTH_SAML_TECHNICAL_CONTACT", None),
                getattr(settings, "SOCIAL_AUTH_SAML_SUPPORT_CONTACT", None),
                getattr(settings, "SOCIAL_AUTH_SAML_ENABLED_IDPS", None),
            ]
        )

        return is_enabled, awx_saml_settings

    def format_config_data(self, awx_settings, type, keys):
        config = {
            "type": f"awx.authentication.authenticator_plugins.{type}",
            "enabled": awx_settings[0],
            "configuration": {},
        }
        for k in keys:
            v = awx_settings[1].get(k)
            config["configuration"].update({k: v})

        return config

    def add_arguments(self, parser):
        parser.add_argument(
            "output_file",
            nargs="?",
            type=str,
            default=None,
            help="Output JSON file path",
        )

    def handle(self, *args, **options):
        try:
            data = []

            # dump SAML settings
            data.append(
                self.format_config_data(
                    self.get_awx_saml_settings(),
                    "saml",
                    self.DAB_SAML_AUTHENTICATOR_KEYS,
                ),
            )

            # write to file if requested
            if options["output_file"]:
                # Define the path for the output JSON file
                output_file = options["output_file"]

                # Ensure the directory exists
                os.makedirs(os.path.dirname(output_file), exist_ok=True)

                # Write data to the JSON file
                with open(output_file, "w") as f:
                    json.dump(data, f, indent=4)

                self.stdout.write(self.style.SUCCESS(f"Auth config data dumped to {output_file}"))
            else:
                self.stdout.write(json.dumps(data, indent=4))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {str(e)}"))
            sys.exit(1)
