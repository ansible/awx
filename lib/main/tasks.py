import os
import subprocess
from celery import task
from lib.main.models import *

@task(name='run_launch_job')
def run_launch_job(launch_job_pk):
    launch_job = LaunchJob.objects.get(pk=launch_job_pk)
    os.environ['ACOM_INVENTORY'] = str(launch_job.inventory.pk)
    inventory_script = os.path.abspath(os.path.join(os.path.dirname(__file__),
        'management', 'commands', 'acom_inventory.py'))
    playbook = launch_job.project.default_playbook
    cmd = ['ansible-playbook', '-i', inventory_script, '-v']
    if False: # local mode
        cmd.extend(['-c', 'local'])
    cmd.append(playbook)
    subprocess.check_call(cmd)
    # FIXME: Do stuff here!
