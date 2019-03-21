Managing Custom Python Dependencies
===================================
awx installations pre-build a special [Python
virtualenv](https://pypi.python.org/pypi/virtualenv) which is automatically
activated for all `ansible-playbook` runs invoked by awx (for example, any time
a Job Template is launched).  By default, this virtualenv is located at
`/var/lib/awx/venv/ansible` on the file system.

awx pre-installs a variety of third-party library/SDK support into this
virtualenv for its integration points with a variety of cloud providers (such
as EC2, OpenStack, Azure, etc...)

Periodically, awx users want to add additional SDK support into this
virtualenv; this documentation describes the supported way to do so.

Preparing a New Custom Virtualenv
=================================
awx allows a _different_ virtualenv to be specified and used on Job Template
runs.  To choose a custom virtualenv, first create one in `/var/lib/awx/venv`:

    $ sudo virtualenv /var/lib/awx/venv/my-custom-venv

Multiple versions of Python are supported, though it's important to note that
the semantics for creating virtualenvs in Python 3 has changed slightly:

    $ sudo python3 -m venv /var/lib/awx/venv/my-custom-venv

Your newly created virtualenv needs a few base dependencies to properly run
playbooks (awx uses memcached as a holding space for playbook artifacts and
fact gathering):

    $ sudo /var/lib/awx/venv/my-custom-venv/bin/pip install python-memcached psutil

From here, you can install _additional_ Python dependencies that you care
about, such as a per-virtualenv version of ansible itself:

    $ sudo /var/lib/awx/venv/my-custom-venv/bin/pip install -U "ansible == X.Y.Z"

...or an additional third-party SDK that's not included with the base awx installation:

    $ sudo /var/lib/awx/venv/my-custom-venv/bin/pip install -U python-digitalocean

If you want to copy them, the libraries included in awx's default virtualenv
can be found using `pip freeze`:

    $ sudo /var/lib/awx/venv/ansible/bin/pip freeze

One important item to keep in mind is that in a clustered awx installation,
you need to ensure that the same custom virtualenv exists on _every_ local file
system at `/var/lib/awx/venv/`.  For container-based deployments, this likely
means building these steps into your own custom image building workflow, e.g.,

```diff
diff --git a/Makefile b/Makefile
index aa8b304..eb05f91 100644
--- a/Makefile
+++ b/Makefile
@@ -164,6 +164,10 @@ requirements_ansible_dev:
        $(VENV_BASE)/ansible/bin/pip install pytest mock; \
    fi
 
+requirements_custom:
+	virtualenv $(VENV_BASE)/my-custom-env
+	$(VENV_BASE)/my-custom-env/bin/pip install python-memcached psutil
+
 requirements_isolated:
    if [ ! -d "$(VENV_BASE)/awx" ]; then \
        virtualenv --system-site-packages $(VENV_BASE)/awx && \
diff --git a/installer/image_build/templates/Dockerfile.j2 b/installer/image_build/templates/Dockerfile.j2
index d69e2c9..a08bae5 100644
--- a/installer/image_build/templates/Dockerfile.j2
+++ b/installer/image_build/templates/Dockerfile.j2
@@ -34,6 +34,7 @@ RUN yum -y install epel-release && \
     pip install virtualenv supervisor && \
     VENV_BASE=/var/lib/awx/venv make requirements_ansible && \
     VENV_BASE=/var/lib/awx/venv make requirements_awx && \
+    VENV_BASE=/var/lib/awx/venv make requirements_custom && \
```

Assigning Custom Virtualenvs
============================
Once you've created a custom virtualenv, you can assign it at the Organization,
Project, or Job Template level:

    PATCH https://awx-host.example.org/api/v2/organizations/N/
    PATCH https://awx-host.example.org/api/v2/projects/N/
    PATCH https://awx-host.example.org/api/v2/job_templates/N/

    Content-Type: application/json
    {
        'custom_virtualenv': '/var/lib/awx/venv/my-custom-venv'
    }

An HTTP `GET` request to `/api/v2/config/` will provide a list of
detected installed virtualenvs:

    {
        "custom_virtualenvs": [
            "/var/lib/awx/venv/my-custom-venv",
            "/var/lib/awx/venv/my-other-custom-venv",
        ],
        ...
    }
