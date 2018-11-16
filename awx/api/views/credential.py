# Copyright (c) 2018 Ansible, Inc.
# All Rights Reserved.

# Django
from django.utils.translation import ugettext_lazy as _

# AWX
from awx.api.generics import SubListAttachDetachAPIView
from awx.api.serializers import CredentialSerializer
from awx.main.models import Credential


class LaunchConfigCredentialsBase(SubListAttachDetachAPIView):

    model = Credential
    serializer_class = CredentialSerializer
    relationship = 'credentials'

    def is_valid_relation(self, parent, sub, created=False):
        if not parent.unified_job_template:
            return {"msg": _("Cannot assign credential when related template is null.")}

        ask_mapping = parent.unified_job_template.get_ask_mapping()

        if self.relationship not in ask_mapping:
            return {"msg": _("Related template cannot accept {} on launch.").format(self.relationship)}
        elif sub.passwords_needed:
            return {"msg": _("Credential that requires user input on launch "
                             "cannot be used in saved launch configuration.")}

        ask_field_name = ask_mapping[self.relationship]

        if not getattr(parent.unified_job_template, ask_field_name):
            return {"msg": _("Related template is not configured to accept credentials on launch.")}
        elif sub.unique_hash() in [cred.unique_hash() for cred in parent.credentials.all()]:
            return {"msg": _("This launch configuration already provides a {credential_type} credential.").format(
                credential_type=sub.unique_hash(display=True))}
        elif sub.pk in parent.unified_job_template.credentials.values_list('pk', flat=True):
            return {"msg": _("Related template already uses {credential_type} credential.").format(
                credential_type=sub.name)}

        # None means there were no validation errors
        return None
