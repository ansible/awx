from urllib.parse import urljoin

from argparse import ArgumentTypeError

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from awx.main.models import Instance, UnifiedJob


class AWXInstance:
    def __init__(self, **filter):
        self.filter = filter
        self.get_instance()

    def get_instance(self):
        filter = self.filter if self.filter is not None else dict(hostname=settings.CLUSTER_HOST_ID)
        qs = Instance.objects.filter(**filter)
        if not qs.exists():
            raise ValueError(f"No AWX instance found with {filter} parameters")
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

    def instance_pretty(self):
        instance = (
            self.instance.hostname,
            urljoin(settings.TOWER_URL_BASE, f"/#/instances/{self.instance.pk}/details"),
        )
        return f"[\"{instance[0]}\"]({instance[1]})"


class Command(BaseCommand):
    help = "Enable instance."

    @staticmethod
    def ge_1(arg):
        if arg == "inf":
            return float("inf")

        int_arg = int(arg)
        if int_arg < 1:
            raise ArgumentTypeError(f"The value must be a positive number >= 1. Provided: \"{arg}\"")
        return int_arg

    def add_arguments(self, parser):
        filter_group = parser.add_mutually_exclusive_group()

        filter_group.add_argument(
            "--hostname",
            type=str,
            default=settings.CLUSTER_HOST_ID,
            help=f"{Instance.hostname.field.help_text} Defaults to the hostname of the machine where the Python interpreter is currently executing".strip(),
        )
        filter_group.add_argument("--id", type=self.ge_1, help=Instance.id.field.help_text)

    def handle(self, *args, **options):
        try:
            filter = dict(id=options["id"]) if options["id"] is not None else dict(hostname=options["hostname"])
            instance = AWXInstance(**filter)
        except ValueError as e:
            raise CommandError(e)

        if instance.enable():
            self.stdout.write(self.style.SUCCESS(f"Instance {instance.instance_pretty()} has been enabled"))
        else:
            self.stdout.write(f"Instance {instance.instance_pretty()} has already been enabled")
