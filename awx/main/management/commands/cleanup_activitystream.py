# Copyright (c) 2015 Ansible, Inc. (formerly AnsibleWorks, Inc.)
# All Rights Reserved.

# Python
import datetime
import logging
from optparse import make_option

# Django
from django.core.management.base import NoArgsCommand
from django.utils.timezone import now

# AWX
from awx.main.models import ActivityStream

class Command(NoArgsCommand):
    '''
    Management command to purge old activity stream events.
    '''

    help = 'Remove old activity stream events from the database'

    option_list = NoArgsCommand.option_list + (
        make_option('--days', dest='days', type='int', default=90, metavar='N',
                    help='Remove activity stream events more than N days old'),
        make_option('--dry-run', dest='dry_run', action='store_true',
                    default=False, help='Dry run mode (show items that would '
                    'be removed)'),)

    def init_logging(self):
        log_levels = dict(enumerate([logging.ERROR, logging.INFO,
                                     logging.DEBUG, 0]))
        self.logger = logging.getLogger('awx.main.commands.cleanup_activitystream')
        self.logger.setLevel(log_levels.get(self.verbosity, 0))
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)
        self.logger.propagate = False

    def cleanup_activitystream(self):
        n_deleted_items = 0
        pks_to_delete = set()
        for asobj in ActivityStream.objects.iterator():
            asobj_disp = '"%s" id: %s' % (unicode(asobj), asobj.id)
            if asobj.timestamp >= self.cutoff:
                if self.dry_run:
                    self.logger.info("would skip %s" % asobj_disp)
            else:
                if self.dry_run:
                    self.logger.info("would delete %s" % asobj_disp)
                else:
                    pks_to_delete.add(asobj.pk)
            # Cleanup objects in batches instead of deleting each one individually.
            if len(pks_to_delete) >= 500:
                ActivityStream.objects.filter(pk__in=pks_to_delete).delete()
                n_deleted_items += len(pks_to_delete)
                pks_to_delete.clear()
        if len(pks_to_delete):
            ActivityStream.objects.filter(pk__in=pks_to_delete).delete()
            n_deleted_items += len(pks_to_delete)
        self.logger.log(99, "Removed %d items", n_deleted_items)

    def handle_noargs(self, **options):
        self.verbosity = int(options.get('verbosity', 1))
        self.init_logging()
        self.days = int(options.get('days', 30))
        self.cutoff = now() - datetime.timedelta(days=self.days)
        self.dry_run = bool(options.get('dry_run', False))
        self.cleanup_activitystream()
