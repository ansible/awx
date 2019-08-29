Usage Examples
==============

Verifying CLI Configuration
---------------------------

To confirm that you've properly configured ``awx`` to point at the correct
AWX/|RHAT| host, and that your authentication credentials are correct, run:

.. code:: bash

    awx config

.. note:: for help configurating authentication settings with the awx CLI, see :ref:`authentication`.

Printing the History of a Particular Job
----------------------------------------

To print a table containing the recent history of any jobs named ``Example Job Template``:

.. code:: bash

    awx jobs list --all --name 'Example Job Template' \
        -f human --filter 'name,created,status'

Creating and Launching a Job Template
-------------------------------------

Assuming you have an existing Inventory named ``Demo Inventory``, here's how
you might set up a new project from a GitHub repository, and run (and monitor
the output of) a playbook from that repository:

.. code:: bash

    export TOWER_COLOR=f
    INVENTORY_ID=$(awx inventory list --name 'Demo Inventory' -f jq --filter '.results[0].id')
    PROJECT_ID=$(awx projects create --wait \
        --organization 1 --name='Example Project' \
        --scm_type git --scm_url 'https://github.com/ansible/ansible-tower-samples' \
        -f jq --filter '.id')
    TEMPLATE_ID=$(awx job_templates create \
        --name='Example Job Template' --project $PROJECT_ID \
        --playbook hello_world.yml --inventory $INVENTORY_ID \
        -f jq --filter '.id')
    awx job_templates launch $TEMPLATE_ID --monitor

Updating a Job Template with Extra Vars
---------------------------------------

.. code:: bash

    awx job_templates modify 1 --extra_vars "@vars.yml"
    awx job_templates modify 1 --extra_vars "@vars.json"
