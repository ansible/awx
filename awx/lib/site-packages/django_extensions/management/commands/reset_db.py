"""
originally from http://www.djangosnippets.org/snippets/828/ by dnordberg
"""

from six.moves import input
from django.conf import settings
from django.core.management.base import CommandError, BaseCommand
import django
import logging
import re
from optparse import make_option


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--noinput', action='store_false',
                    dest='interactive', default=True,
                    help='Tells Django to NOT prompt the user for input of any kind.'),
        make_option('--no-utf8', action='store_true',
                    dest='no_utf8_support', default=False,
                    help='Tells Django to not create a UTF-8 charset database'),
        make_option('-U', '--user', action='store',
                    dest='user', default=None,
                    help='Use another user for the database then defined in settings.py'),
        make_option('-P', '--password', action='store',
                    dest='password', default=None,
                    help='Use another password for the database then defined in settings.py'),
        make_option('-D', '--dbname', action='store',
                    dest='dbname', default=None,
                    help='Use another database name then defined in settings.py (For PostgreSQL this defaults to "template1")'),
        make_option('-R', '--router', action='store',
                    dest='router', default=None,
                    help='Use this router-database other then defined in settings.py'),
    )
    help = "Resets the database for this project."

    def set_db_settings(self, *args, **options):
        if django.get_version() >= "1.2":
            router = options.get('router')
            if router is None:
                return False

            # retrieve this with the 'using' argument
            dbinfo = settings.DATABASES.get(router)
            settings.DATABASE_ENGINE = dbinfo.get('ENGINE').split('.')[-1]
            settings.DATABASE_USER = dbinfo.get('USER')
            settings.DATABASE_PASSWORD = dbinfo.get('PASSWORD')
            settings.DATABASE_NAME = dbinfo.get('NAME')
            settings.DATABASE_HOST = dbinfo.get('HOST')
            settings.DATABASE_PORT = dbinfo.get('PORT')
            return True
        else:
            # settings are set for django < 1.2 no modification needed
            return True

    def handle(self, *args, **options):
        """
        Resets the database for this project.

        Note: Transaction wrappers are in reverse as a work around for
        autocommit, anybody know how to do this the right way?
        """

        if django.get_version() >= "1.2":
            got_db_settings = self.set_db_settings(*args, **options)
            if not got_db_settings:
                raise CommandError("You are using Django %s which requires to specify the db-router.\nPlease specify the router by adding --router=<routername> to this command." % django.get_version())
                return

        verbosity = int(options.get('verbosity', 1))
        if options.get('interactive'):
            confirm = input("""
You have requested a database reset.
This will IRREVERSIBLY DESTROY
ALL data in the database "%s".
Are you sure you want to do this?

Type 'yes' to continue, or 'no' to cancel: """ % (settings.DATABASE_NAME,))
        else:
            confirm = 'yes'

        if confirm != 'yes':
            print("Reset cancelled.")
            return

        postgis = re.compile('.*postgis')
        engine = settings.DATABASE_ENGINE
        user = options.get('user', settings.DATABASE_USER)
        if user is None:
            user = settings.DATABASE_USER
        password = options.get('password', settings.DATABASE_PASSWORD)
        if password is None:
            password = settings.DATABASE_PASSWORD

        if engine in ('sqlite3', 'spatialite'):
            import os
            try:
                logging.info("Unlinking %s database" % engine)
                os.unlink(settings.DATABASE_NAME)
            except OSError:
                pass
        elif engine == 'mysql':
            import MySQLdb as Database
            kwargs = {
                'user': user,
                'passwd': password,
            }
            if settings.DATABASE_HOST.startswith('/'):
                kwargs['unix_socket'] = settings.DATABASE_HOST
            else:
                kwargs['host'] = settings.DATABASE_HOST
            if settings.DATABASE_PORT:
                kwargs['port'] = int(settings.DATABASE_PORT)

            connection = Database.connect(**kwargs)
            drop_query = 'DROP DATABASE IF EXISTS `%s`' % settings.DATABASE_NAME
            utf8_support = options.get('no_utf8_support', False) and '' or 'CHARACTER SET utf8'
            create_query = 'CREATE DATABASE `%s` %s' % (settings.DATABASE_NAME, utf8_support)
            logging.info('Executing... "' + drop_query + '"')
            connection.query(drop_query)
            logging.info('Executing... "' + create_query + '"')
            connection.query(create_query)

        elif engine == 'postgresql' or engine == 'postgresql_psycopg2' or postgis.match(engine):
            if engine == 'postgresql':
                import psycopg as Database  # NOQA
            elif engine == 'postgresql_psycopg2' or postgis.match(engine):
                import psycopg2 as Database  # NOQA

            if settings.DATABASE_NAME == '':
                from django.core.exceptions import ImproperlyConfigured
                raise ImproperlyConfigured("You need to specify DATABASE_NAME in your Django settings file.")

            database_name = options.get('dbname', 'template1')
            if options.get('dbname') is None:
                database_name = 'template1'
            conn_string = "dbname=%s" % database_name
            if settings.DATABASE_USER:
                conn_string += " user=%s" % user
            if settings.DATABASE_PASSWORD:
                conn_string += " password='%s'" % password
            if settings.DATABASE_HOST:
                conn_string += " host=%s" % settings.DATABASE_HOST
            if settings.DATABASE_PORT:
                conn_string += " port=%s" % settings.DATABASE_PORT

            connection = Database.connect(conn_string)
            connection.set_isolation_level(0)  # autocommit false
            cursor = connection.cursor()
            drop_query = 'DROP DATABASE %s' % settings.DATABASE_NAME
            logging.info('Executing... "' + drop_query + '"')

            try:
                cursor.execute(drop_query)
            except Database.ProgrammingError as e:
                logging.info("Error: %s" % str(e))

            # Encoding should be SQL_ASCII (7-bit postgres default) or prefered UTF8 (8-bit)
            create_query = "CREATE DATABASE %s" % settings.DATABASE_NAME
            if settings.DATABASE_USER:
                create_query += " WITH OWNER = %s " % settings.DATABASE_USER
            create_query += " ENCODING = 'UTF8'"

            if postgis.match(engine):
                create_query += ' TEMPLATE = template_postgis'
            if settings.DEFAULT_TABLESPACE:
                create_query += ' TABLESPACE = %s;' % settings.DEFAULT_TABLESPACE
            else:
                create_query += ';'
            logging.info('Executing... "' + create_query + '"')
            cursor.execute(create_query)

        else:
            raise CommandError("Unknown database engine %s" % engine)

        if verbosity >= 2 or options.get('interactive'):
            print("Reset successful.")
