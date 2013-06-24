from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
import getpass


class Command(BaseCommand):
    help = "Clone of the UNIX program ``passwd'', for django.contrib.auth."

    requires_model_validation = False

    def handle(self, *args, **options):
        if len(args) > 1:
            raise CommandError("need exactly one or zero arguments for username")

        if args:
            username, = args
        else:
            username = getpass.getuser()

        try:
            u = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError("user %s does not exist" % username)

        print("Changing password for user: %s" % u.username)
        p1 = p2 = ""
        while "" in (p1, p2) or p1 != p2:
            p1 = getpass.getpass()
            p2 = getpass.getpass("Password (again): ")
            if p1 != p2:
                print("Passwords do not match, try again")
            elif "" in (p1, p2):
                raise CommandError("aborted")

        u.set_password(p1)
        u.save()

        return "Password changed successfully for user %s\n" % u.username
