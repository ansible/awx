import socket
import time
from urllib.parse import urljoin

from argparse import ArgumentTypeError

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils.timezone import now

from awx.main.models import Instance, UnifiedJob


class AWXInstance():
    def __init__(self, **filter):
        self.filter = filter
        self.get_instance()

    def get_instance(self):
        filter = self.filter if self.filter is not None else dict(hostname=socket.gethostname())
        qs = Instance.objects.filter(**filter)
        if not qs.exists():
            raise ValueError(f"No AWX instance found with {filter} "\
                             "parameters")
        self.instance = qs.first()

    def disable(self):
        if self.instance.enabled:
            self.instance.enabled = False
            self.instance.save()
            return True

    def enable(self):
        if not self.instance.enabled:
            self.instance.enabled = True
            self.instance.save()
            return True

    def jobs(self):
        return UnifiedJob.objects.filter(
            Q(controller_node=self.instance.hostname) | Q(execution_node=self.instance.hostname),
            status__in=("running", "waiting")
        )

    def jobs_pretty(self):
        jobs = []
        for j in self.jobs():
            # similar calculation of `elapsed` as the corresponding serializer
            # does
            td = now() - j.started
            elapsed = (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / (10**6 * 1.0)
            elapsed = float(elapsed)
            details = dict(
                name    = j.name,
                url     = j.get_ui_url(),
                elapsed = elapsed,
            )
            jobs.append(details)

        jobs = sorted(jobs, reverse=True, key=lambda j: j["elapsed"])

        return ", ".join(
            [f"[\"{j['name']}\"]({j['url']})" for j in jobs]
        )

    def instance_pretty(self):
        instance = (
            self.instance.hostname,
            urljoin(settings.TOWER_URL_BASE, f"/#/instances/{self.instance.pk}/details"),
        )
        return f"[\"{instance[0]}\"]({instance[1]})"


class Command(BaseCommand):
    help = "Disable instance, optionally waiting for all its managed jobs " \
           "to finish."

    @staticmethod
    def int_positive(arg):
        int_arg = int(arg)
        if int_arg < 1:
            raise ArgumentTypeError(f"The value must be a positive number >= 1. Provided: \"{arg}\"")
        return int_arg

    def add_arguments(self, parser):
        filter_group = parser.add_mutually_exclusive_group()

        filter_group.add_argument("--hostname", type=str,
            default=socket.gethostname(),
            help=f"{Instance.hostname.field.help_text} Defaults to the " \
                "hostname of the machine where the Python interpreter is " \
                "currently executing".strip()
        )
        filter_group.add_argument("--id", type=self.int_positive,
            help=Instance.id.field.help_text
        )

        parser.add_argument("--wait", action="store_true",
            help="Wait for jobs managed by the instance to finish. With " \
                "default retry arguments waits for about 3h",
        )

        parser.add_argument("--retry", type=self.int_positive, default=360,
            help="Number of retries when waiting for jobs to finish. " \
                "Default: 360",
        )

        parser.add_argument("--retry_sleep", type=self.int_positive, default=30,
            help="Number of seconds to sleep before consequtive retries " \
                "when waiting. Default: 30",
        )

    def handle(self, *args, **options):
        try:
            filter = dict(id=options["id"]) if options["id"] is not None else dict(hostname=options["hostname"])
            instance = AWXInstance(**filter)
        except ValueError as e:
            raise CommandError(e)

        if instance.disable():
            self.stdout.write(self.style.SUCCESS(
                f"Instance {instance.instance_pretty()} has been disabled"
            ))
        else:
            self.stdout.write(
                f"Instance {instance.instance_pretty()} has already been disabled"
            )

        if not options["wait"]:
            return

        rc = 1
        while instance.jobs().count() > 0:
            if rc < options["retry"]:
                self.stdout.write(
                    f"{rc}/{options['retry']}: " \
                    f"Waiting {options['retry_sleep']}s before the next " \
                    "attempt to see if the following instance' managed jobs " \
                    f"have finished: {instance.jobs_pretty()}"
                )
                rc += 1
                time.sleep(options["retry_sleep"])
            else:
                raise CommandError(
                    f"{rc}/{options['retry']}: " \
                    "No more retry attempts left, but the instance still " \
                    f"has associated managed jobs: {instance.jobs_pretty()}"
                )
        else:
            self.stdout.write(self.style.SUCCESS(
                "Done waiting for instance' managed jobs to finish!"
            ))
