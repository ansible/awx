from django.core.management.base import BaseCommand
import requests

from awx.main.models import Credential, CredentialType


class Command(BaseCommand):
    """List name and digest given an automation hub repository name"""

    help = 'List name and digest given an automation hub repository name.'

    def add_arguments(self, parser):
        parser.add_argument("repository_name", type=str)
        parser.add_argument("--credential_name", type=str)

    def handle(self, *args, **options):
        repo_name = options["repository_name"]
        cred_name = options["credential_name"]

        cred_type = CredentialType.objects.get(namespace="registry")
        cred = Credential.objects.get(name=cred_name, credential_type=cred_type)

        request_host = cred.get_input("host")
        request_url = f"https://{request_host}/api/galaxy/_ui/v1/execution-environments/repositories/{repo_name}/_content/tags/"
        request_auth = (cred.get_input("username"), cred.get_input("password"))

        response = requests.get(request_url, auth=request_auth, verify=False)
        response.raise_for_status()

        for item in response.json()["data"]:
            print(f"{item['name']} --- {item['tagged_manifest']['digest']}")
