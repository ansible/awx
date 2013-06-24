from django.core.management.base import LabelCommand
from optparse import make_option
from django_extensions.management.jobs import get_jobs, print_jobs


class Command(LabelCommand):
    option_list = LabelCommand.option_list + (
        make_option('--list', '-l', action="store_true", dest="list_jobs",
                    help="List all jobs with their description"),
    )
    help = "Runs scheduled maintenance jobs."
    args = "[minutely quarter_hourly hourly daily weekly monthly yearly]"
    label = ""

    requires_model_validation = True

    def usage_msg(self):
        print("Run scheduled jobs. Please specify 'minutely', 'quarter_hourly', 'hourly', 'daily', 'weekly', 'monthly' or 'yearly'")

    def runjobs(self, when, options):
        verbosity = int(options.get('verbosity', 1))
        jobs = get_jobs(when, only_scheduled=True)
        list = jobs.keys()
        list.sort()
        for app_name, job_name in list:
            job = jobs[(app_name, job_name)]
            if verbosity > 1:
                print("Executing %s job: %s (app: %s)" % (when, job_name, app_name))
            try:
                job().execute()
            except Exception:
                import traceback
                print("ERROR OCCURED IN %s JOB: %s (APP: %s)" % (when.upper(), job_name, app_name))
                print("START TRACEBACK:")
                traceback.print_exc()
                print("END TRACEBACK\n")

    def runjobs_by_signals(self, when, options):
        """ Run jobs from the signals """
        # Thanks for Ian Holsman for the idea and code
        from django_extensions.management import signals
        from django.db import models
        from django.conf import settings

        verbosity = int(options.get('verbosity', 1))
        for app_name in settings.INSTALLED_APPS:
            try:
                __import__(app_name + '.management', '', '', [''])
            except ImportError:
                pass

        for app in models.get_apps():
            if verbosity > 1:
                app_name = '.'.join(app.__name__.rsplit('.')[:-1])
                print("Sending %s job signal for: %s" % (when, app_name))
            if when == 'minutely':
                signals.run_minutely_jobs.send(sender=app, app=app)
            elif when == 'quarter_hourly':
                signals.run_quarter_hourly_jobs.send(sender=app, app=app)
            elif when == 'hourly':
                signals.run_hourly_jobs.send(sender=app, app=app)
            elif when == 'daily':
                signals.run_daily_jobs.send(sender=app, app=app)
            elif when == 'weekly':
                signals.run_weekly_jobs.send(sender=app, app=app)
            elif when == 'monthly':
                signals.run_monthly_jobs.send(sender=app, app=app)
            elif when == 'yearly':
                signals.run_yearly_jobs.send(sender=app, app=app)

    def handle(self, *args, **options):
        when = None
        if len(args) > 1:
            self.usage_msg()
            return
        elif len(args) == 1:
            if not args[0] in ['minutely', 'quarter_hourly', 'hourly', 'daily', 'weekly', 'monthly', 'yearly']:
                self.usage_msg()
                return
            else:
                when = args[0]
        if options.get('list_jobs'):
            print_jobs(when, only_scheduled=True, show_when=True, show_appname=True)
        else:
            if not when:
                self.usage_msg()
                return
            self.runjobs(when, options)
            self.runjobs_by_signals(when, options)

# Backwards compatibility for Django r9110
if not [opt for opt in Command.option_list if opt.dest == 'verbosity']:
    Command.option_list += (
        make_option('--verbosity', '-v', action="store", dest="verbosity",
                    default='1', type='choice', choices=['0', '1', '2'],
                    help="Verbosity level; 0=minimal output, 1=normal output, 2=all output"),
    )
