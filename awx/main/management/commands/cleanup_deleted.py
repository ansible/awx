# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import datetime
import logging
from optparse import make_option

# Django
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.auth.models import User
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now, is_aware, make_aware

# AWX
from awx.main.models import *

class Command(BaseCommand):
    '''
    Management command to cleanup deleted items.
    '''

    help = 'Cleanup deleted items from the database.'
    args = '[<appname>, <appname.ModelName>, ...]'

    option_list = BaseCommand.option_list + (
        make_option('--days', dest='days', type='int', default=90, metavar='N',
                    help='Remove items deleted more than N days ago'),
        make_option('--dry-run', dest='dry_run', action='store_true',
                    default=False, help='Dry run mode (show items that would '
                    'be removed)'),
    )

    def get_models(self, model):
        if not model._meta.abstract:
            yield model
        for sub in model.__subclasses__():
            for submodel in self.get_models(sub):
                yield submodel

    def cleanup_model(self, model):
        name_field = None
        active_field = None
        for field in model._meta.fields:
            if field.name in ('name', 'username'):
                name_field = field.name
            if field.name in ('is_active', 'active'):
                active_field = field.name
        if not name_field:
            self.logger.warning('skipping model %s, no name field', model)
            return
        if not active_field:
            self.logger.warning('skipping model %s, no active field', model)
            return
        if name_field == 'username' and active_field == 'is_active':
            name_prefix = '_d_'
        else:
            name_prefix = '_deleted_'
        qs = model.objects.filter(**{
            active_field: False,
            '%s__startswith' % name_field: name_prefix,
        })
        self.logger.debug('cleaning up model %s', model)
        for instance in qs:
            dt = parse_datetime(getattr(instance, name_field).split('_')[2])
            if not is_aware(dt):
                dt = make_aware(dt, self.cutoff.tzinfo)
            if not dt:
                self.logger.warning('unable to find deleted timestamp in %s '
                                    'field', name_field)
            elif dt >= self.cutoff:
                action_text = 'would skip' if self.dry_run else 'skipping'
                self.logger.debug('%s %s', action_text, instance)
            else:
                action_text = 'would delete' if self.dry_run else 'deleting'
                self.logger.info('%s %s', action_text, instance)
                if not self.dry_run:
                    instance.delete()

    def init_logging(self):
        log_levels = dict(enumerate([logging.ERROR, logging.INFO,
                                     logging.DEBUG, 0]))
        self.logger = logging.getLogger('awx.main.commands.cleanup_deleted')
        self.logger.setLevel(log_levels.get(self.verbosity, 0))
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)
        self.logger.propagate = False

    @transaction.commit_on_success
    def handle(self, *args, **options):
        self.verbosity = int(options.get('verbosity', 1))
        self.init_logging()
        self.days = int(options.get('days', 90))
        self.dry_run = bool(options.get('dry_run', False))
        # FIXME: Handle args to select models.
        self.cutoff = now() - datetime.timedelta(days=self.days)
        self.cleanup_model(User)
        for model in self.get_models(PrimordialModel):
            self.cleanup_model(model)
