from django.core.management.base import BaseCommand

from awx.main.tasks import profile_sql


class Command(BaseCommand):
    """
    Enable or disable SQL Profiling across all Python processes.
    SQL profile data will be recorded at /var/log/tower/profile
    """

    def add_arguments(self, parser):
        parser.add_argument('--threshold', dest='threshold', type=float, default=2.0,
                            help='The minimum query duration in seconds (default=2).  Use 0 to disable.')
        parser.add_argument('--minutes', dest='minutes', type=float, default=5,
                            help='How long to record for in minutes (default=5)')

    def handle(self, **options):
        profile_sql.delay(
            threshold=options['threshold'], minutes=options['minutes']
        )
        if options['threshold'] > 0:
            print(f"SQL profiling initiated with a threshold of {options['threshold']} second(s) and a"
                  f" duration of {options['minutes']} minute(s), any queries that meet criteria can"
                  f" be found in /var/log/tower/profile/.")
        else:
            print("SQL profiling disabled.")
