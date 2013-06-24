from random import choice
from django.core.management.base import NoArgsCommand


class Command(NoArgsCommand):
    help = "Generates a new SECRET_KEY that can be used in a project settings file."

    requires_model_validation = False

    def handle_noargs(self, **options):
        return ''.join([choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)])
