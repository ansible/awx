# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import threading

# Monkeypatch xmlsec.initialize() to only run once (https://github.com/ansible/ansible-tower/issues/3241).
xmlsec_init_lock = threading.Lock()
xmlsec_initialized = False

import dm.xmlsec.binding # noqa
original_xmlsec_initialize = dm.xmlsec.binding.initialize


def xmlsec_initialize(*args, **kwargs):
    global xmlsec_init_lock, xmlsec_initialized, original_xmlsec_initialize
    with xmlsec_init_lock:
        if not xmlsec_initialized:
            original_xmlsec_initialize(*args, **kwargs)
            xmlsec_initialized = True


dm.xmlsec.binding.initialize = xmlsec_initialize


default_app_config = 'awx.sso.apps.SSOConfig'
