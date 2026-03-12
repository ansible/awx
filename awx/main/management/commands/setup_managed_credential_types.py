# Copyright (c) 2019 Ansible by Red Hat
# All Rights Reserved.

from django.core.management.base import BaseCommand

from awx.main.models import CredentialType


class Command(BaseCommand):
    help = 'Load default managed credential types.'

    def handle(self, *args, **options):
        """
        Note that the call below is almost redundant. The same call as below is called in the Django ready() code path. The ready() code path runs
        before every management command. The one difference in the below call is that the below call is _more_ likely to _actually_ run. The ready() code path
        version _can_ be a NOOP if the lock is not acquired. The below version waits to acquire the lock. This can be useful for recreating bugs or pdb.
        """
        CredentialType.setup_tower_managed_defaults(wait_for_lock=True)
