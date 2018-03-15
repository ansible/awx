# Copyright (c) 2018 Ansible by Red Hat
# All Rights Reserved.

# Django
from django.utils.translation import ugettext_lazy as _

# Django REST Framework
from rest_framework.exceptions import ValidationError


class ActiveJobConflict(ValidationError):
    status_code = 409

    def __init__(self, active_jobs):
        super(ActiveJobConflict, self).__init__({
            "error": _("Resource is being used by running jobs."),
            "active_jobs": active_jobs
        })
