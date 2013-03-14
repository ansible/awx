from celery import task
from lib.main.models import *

@task(name='run_launch_job')
def run_launch_job(launch_job_pk):
    launch_job = LaunchJob.objects.get(pk=launch_job_pk)
    # FIXME: Do stuff here!
