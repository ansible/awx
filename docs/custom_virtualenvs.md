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
runs.  To choose a custom virtualenv, first we need to create one. Here, we are
using `/opt/my-envs/` as the directory to hold custom venvs. But you can use any
other directory and replace `/opt/my-envs/` with that. Let's create the directory
first if absent:

    $ sudo mkdir /opt/my-envs

Now, we need to tell Tower to look into this directory for custom venvs. For that,
we can add this directory to the `CUSTOM_VENV_PATHS` setting as:

    $ HTTP PATCH /api/v2/settings/system/ {'CUSTOM_VENV_PATHS': ["/opt/my-envs/"]}

If we have venvs spanned over multiple directories, we can add all the paths and
Tower will aggregate venvs from them:

    $ HTTP PATCH /api/v2/settings/system/ {'CUSTOM_VENV_PATHS': ["/path/1/to/venv/",
                                                                "/path/2/to/venv/",
                                                                "/path/3/to/venv/"]}

Now that we have the directory setup, we can create a virtual environment in that using:

    $ sudo virtualenv /opt/my-envs/custom-venv

Multiple versions of Python are supported, though it's important to note that
the semantics for creating virtualenvs in Python 3 has changed slightly:

    $ sudo python3 -m venv /opt/my-envs/custom-venv

Your newly created virtualenv needs a few base dependencies to properly run
playbooks:
fact gathering):

    $ sudo /opt/my-envs/custom-venv/bin/pip install psutil

From here, you can install _additional_ Python dependencies that you care
about, such as a per-virtualenv version of ansible itself:

    $ sudo /opt/my-envs/custom-venv/bin/pip install -U "ansible == X.Y.Z"

...or an additional third-party SDK that's not included with the base awx installation:

    $ sudo /opt/my-envs/custom-venv/bin/pip install -U python-digitalocean

If you want to copy them, the libraries included in awx's default virtualenv
can be found using `pip freeze`:

    $ sudo /var/lib/awx/venv/ansible/bin/pip freeze

One important item to keep in mind is that in a clustered awx installation,
you need to ensure that the same custom virtualenv exists on _every_ local file
system at `/opt/my-envs/`.  For container-based deployments, this likely
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
+ mkdir -p /opt/my-envs
+	virtualenv /opt/my-envs/my-custom-env
+	/opt/my-envs/my-custom-env/bin/pip install psutil
+
diff --git a/installer/roles/image_build/templates/Dockerfile.j2 b/installer/roles/image_build/templates/Dockerfile.j2
index d3b582ffcb..220ac760a3 100644
--- a/installer/roles/image_build/templates/Dockerfile.j2
+++ b/installer/roles/image_build/templates/Dockerfile.j2
@@ -165,6 +165,7 @@ RUN openssl req -nodes -newkey rsa:2048 -keyout /etc/nginx/nginx.key -out /etc/n
     chmod 640 /etc/nginx/nginx.{csr,key,crt}
 {% else %}
 COPY --from=builder /var/lib/awx /var/lib/awx
+COPY --from=builder /opt/my-envs /opt/my-envs
 RUN ln -s /var/lib/awx/venv/awx/bin/awx-manage /usr/bin/awx-manage
 {% endif %}
```

Once the AWX API is available, update the `CUSTOM_VENV_PATHS` setting as described in `Preparing a New Custom Virtualenv`.

Kubernetes Custom Virtualenvs
=============================
You can add custom virtual environments without modifying images by including
the following variables in your `install.yml` playbook run. Your variables file
must have a variable called `custom_venvs` with a list of your custom
virtualenvs containing the name, python interpreter, ansible version, and a list
of modules that should be installed in each one:

```yaml
# venv_vars.yaml
---
custom_venvs:
  - name: dns_team
    python: python3 # Defaults to python2
    python_ansible_version: 2.8.1
    python_modules:
      - dnspython
      - infoblox-client
  - name: windows_team
    python: python2
    python_ansible_version: 2.8.0
    python_modules:
      - winrm
  - name: vmware_team
    python_ansible_version: 2.7.10
    python_modules:
      - pyvmomi
```

The virtualenvs will be created in `/opt/custom-venvs` by default, but you can
override that location by setting the variable `custom_venvs_path`.

You can use the variables file like so:

    $ ansible-playbook -i inventory install.yml --extra-vars "@venv_vars.yaml"

Once the AWX API is available, you will need to update the `CUSTOM_VENV_PATHS`
setting as described in `Preparing a New Custom Virtualenv`.

Assigning Custom Virtualenvs
============================
Once you've created a custom virtualenv, you can assign it at the Organization,
Project, or Job Template level:

```http
PATCH https://awx-host.example.org/api/v2/organizations/N/
PATCH https://awx-host.example.org/api/v2/projects/N/
PATCH https://awx-host.example.org/api/v2/job_templates/N/

Content-Type: application/json
{
    "custom_virtualenv": "/opt/my-envs/custom-venv/"
}
```

An HTTP `GET` request to `/api/v2/config/` will provide a list of
detected installed virtualenvs:

    {
        "custom_virtualenvs": [
            "/opt/my-envs/custom-venv/",
            "/opt/my-envs/my-other-custom-venv/",
        ],
        ...
    }
