import json
import os
import sys
from typing import Any

from django.core.management.base import BaseCommand
from django.conf import settings

from awx.conf import settings_registry


class Command(BaseCommand):
    help = 'Dump the current auth configuration in django_ansible_base.authenticator format, currently supports SAML'

    DAB_SAML_AUTHENTICATOR_KEYS = {
        "SP_ENTITY_ID": True,
        "SP_PUBLIC_CERT": True,
        "SP_PRIVATE_KEY": True,
        "ORG_INFO": True,
        "TECHNICAL_CONTACT": True,
        "SUPPORT_CONTACT": True,
        "SP_EXTRA": False,
        "SECURITY_CONFIG": False,
        "EXTRA_DATA": False,
        "ENABLED_IDPS": True,
        "CALLBACK_URL": False,
    }

    def is_enabled(self, settings, keys):
        missing_fields = []
        for key, required in keys.items():
            if required and not settings.get(key):
                missing_fields.append(key)
        if missing_fields:
            return False, missing_fields
        return True, None

    def get_awx_saml_settings(self) -> dict[str, Any]:
        awx_saml_settings = {}
        for awx_saml_setting in settings_registry.get_registered_settings(category_slug='saml'):
            awx_saml_settings[awx_saml_setting.removeprefix("SOCIAL_AUTH_SAML_")] = getattr(settings, awx_saml_setting, None)

        return awx_saml_settings

    def format_config_data(self, enabled, awx_settings, type, keys, name):
        config = {
            "type": f"ansible_base.authentication.authenticator_plugins.{type}",
            "name": name,
            "enabled": enabled,
            "create_objects": True,
            "users_unique": False,
            "remove_users": True,
            "configuration": {},
        }
        for k in keys:
            v = awx_settings.get(k)
            config["configuration"].update({k: v})

        if type == "saml":
            idp_to_key_mapping = {
                "url": "IDP_URL",
                "x509cert": "IDP_X509_CERT",
                "entity_id": "IDP_ENTITY_ID",
                "attr_email": "IDP_ATTR_EMAIL",
                "attr_groups": "IDP_GROUPS",
                "attr_username": "IDP_ATTR_USERNAME",
                "attr_last_name": "IDP_ATTR_LAST_NAME",
                "attr_first_name": "IDP_ATTR_FIRST_NAME",
                "attr_user_permanent_id": "IDP_ATTR_USER_PERMANENT_ID",
            }
            for idp_name in awx_settings.get("ENABLED_IDPS", {}):
                for key in idp_to_key_mapping:
                    value = awx_settings["ENABLED_IDPS"][idp_name].get(key)
                    if value is not None:
                        config["name"] = idp_name
                        config["configuration"].update({idp_to_key_mapping[key]: value})

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
            awx_saml_settings = self.get_awx_saml_settings()
            awx_saml_enabled, saml_missing_fields = self.is_enabled(awx_saml_settings, self.DAB_SAML_AUTHENTICATOR_KEYS)
            if awx_saml_enabled:
                awx_saml_name = awx_saml_settings["ENABLED_IDPS"]
                data.append(
                    self.format_config_data(
                        awx_saml_enabled,
                        awx_saml_settings,
                        "saml",
                        self.DAB_SAML_AUTHENTICATOR_KEYS,
                        awx_saml_name,
                    )
                )
            else:
                data.append({"SAML_missing_fields": saml_missing_fields})

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
