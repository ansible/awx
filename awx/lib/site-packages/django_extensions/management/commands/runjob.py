from django.core.management.base import LabelCommand
from optparse import make_option
from django_extensions.management.jobs import get_job, print_jobs


class Command(LabelCommand):
    option_list = LabelCommand.option_list + (
        make_option('--list', '-l', action="store_true", dest="list_jobs",
                    help="List all jobs with their description"),
    )
    help = "Run a single maintenance job."
    args = "[app_name] job_name"
    label = ""

    requires_model_validation = True

    def runjob(self, app_name, job_name, options):
        verbosity = int(options.get('verbosity', 1))
        if verbosity > 1:
            print("Executing job: %s (app: %s)" % (job_name, app_name))
        try:
            job = get_job(app_name, job_name)
        except KeyError:
            if app_name:
                print("Error: Job %s for applabel %s not found" % (app_name, job_name))
            else:
                print("Error: Job %s not found" % job_name)
            print("Use -l option to view all the available jobs")
            return
        try:
            job().execute()
        except Exception:
            import traceback
            print("ERROR OCCURED IN JOB: %s (APP: %s)" % (job_name, app_name))
            print("START TRACEBACK:")
            traceback.print_exc()
            print("END TRACEBACK\n")

    def handle(self, *args, **options):
        app_name = None
        job_name = None
        if len(args) == 1:
            job_name = args[0]
        elif len(args) == 2:
            app_name, job_name = args
        if options.get('list_jobs'):
            print_jobs(only_scheduled=False, show_when=True, show_appname=True)
        else:
            if not job_name:
                print("Run a single maintenance job. Please specify the name of the job.")
                return
            self.runjob(app_name, job_name, options)
