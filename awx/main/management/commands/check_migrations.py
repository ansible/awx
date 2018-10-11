from django.db import connections
from django.db.backends.sqlite3.base import DatabaseWrapper
from django.core.management.commands.makemigrations import Command as MakeMigrations


class Command(MakeMigrations):

    def execute(self, *args, **options):
        settings = connections['default'].settings_dict.copy()
        settings['ENGINE'] = 'sqlite3'
        connections['default'] = DatabaseWrapper(settings)
        return MakeMigrations().execute(*args, **options)
