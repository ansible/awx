import requests
from urllib.parse import urljoin, quote
import warnings

from django.core import management
from django.core.management.base import BaseCommand

from awx.main.models import Credential, CredentialType


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("credential_name")
        parser.add_argument("--insecure", action="store_true", default=False)

    def handle(self, *args, **options):
        cred_name = options["credential_name"]
        insecure = options["insecure"]

        cred_type = CredentialType.objects.get(namespace="registry")
        cred = Credential.objects.get(name=cred_name, credential_type=cred_type)

        request_host = cred.get_input("host")
        request_url = f"https://{request_host}/api/galaxy/_ui/v1/execution-environments/repositories/"
        request_auth = (
            cred.get_input("username"),
            cred.get_input("password"),
        )
        with warnings.catch_warnings():
            if insecure:
                warnings.simplefilter("ignore")
            response = requests.get(request_url, auth=request_auth, verify=not insecure)
        response.raise_for_status()

        for item in response.json()["data"]:
            print(item["name"])
