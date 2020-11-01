# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.
import os
import logging
import django
from awx import __version__ as tower_version
# Prepare the AWX environment.
from awx import prepare_env, MODE
from channels.routing import get_default_application  # noqa
prepare_env() # NOQA



"""
ASGI config for AWX project.

It exposes the ASGI callable as a module-level variable named ``channel_layer``.

For more information on this file, see
https://channels.readthedocs.io/en/latest/deploying.html
"""

if MODE == 'production':
    logger = logging.getLogger('awx.main.models.jobs')
    try:
        fd = open("/var/lib/awx/.tower_version", "r")
        if fd.read().strip() != tower_version:
            raise ValueError()
    except FileNotFoundError:
        pass
    except ValueError as e:
        logger.error("Missing or incorrect metadata for Tower version.  Ensure Tower was installed using the setup playbook.")
        raise Exception("Missing or incorrect metadata for Tower version.  Ensure Tower was installed using the setup playbook.") from e


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "awx.settings")
django.setup()
channel_layer = get_default_application()
