# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import datetime
from optparse import make_option

# Django
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.models import User
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now, is_aware, make_aware
from django.core.management.base import CommandError

# AWX
from awx.main.models import * # noqa

class Command(BaseCommand):
    '''
    Management command to age deleted items.
    '''

    help = 'Age deleted items in the database.'

    option_list = BaseCommand.option_list + (
        make_option('--days', dest='days', type='int', default=90, metavar='N',
                    help='Age deleted items N days (90 if not specified)'),
        make_option('--id', dest='id', type='int', default=None,
                    help='Object primary key'),
        make_option('--type', dest='type', default=None,
                    help='Model to limit aging to'),
    )

    def get_models(self, model):
        if not model._meta.abstract:
            yield model
        for sub in model.__subclasses__():
            for submodel in self.get_models(sub):
                yield submodel

    def cleanup_model(self, model, id=None):
        '''
        Presume the '_deleted_' string to be in the 'name' field unless considering the User model.
        When considering the User model, presume the '_d_' string to be in the 'username' field.
        '''
        name_field = 'name'
        name_prefix = '_deleted_'
        n_aged_items = 0
        if model is User:
            name_field = 'username'
            name_prefix = '_d_'
        active_field = None
        for field in model._meta.fields:
            if field.name in ('is_active', 'active'):
                active_field = field.name
        if not active_field:
            #print("Skipping model %s, no active field" % model)
            print("Returning %s" % n_aged_items)
            return n_aged_items

        kv = {
            active_field: False,
        }
        if id:
            kv['pk'] = id
        else:
            kv['%s__startswith' % name_field] = name_prefix

        qs = model.objects.filter(**kv)
        #print("Aging model %s" % model)
        for instance in qs:
            name = getattr(instance, name_field)
            name_pieces = name.split('_')
            if not name_pieces or len(name_pieces) < 3:
                print("Unexpected deleted model name format %s" % name)
                return n_aged_items

            if len(name_pieces) <= 3:
                name_append = ''
            else:
                name_append = '_' + name_pieces[3]

            dt = parse_datetime(name_pieces[2])
            if not is_aware(dt):
                dt = make_aware(dt, self.cutoff.tzinfo)
            if not dt:
                print('unable to find deleted timestamp in %s field' % name_field)
            else:
                aged_date = dt - datetime.timedelta(days=self.days)
                instance.name = name_prefix + aged_date.isoformat() + name_append
                instance.save()
                #print("Aged %s" % instance.name)
                n_aged_items += 1



        return n_aged_items

    @transaction.atomic
    def handle(self, *args, **options):
        self.days = int(options.get('days', 90))
        self.id = options.get('id', None)
        self.type = options.get('type', None)
        self.cutoff = now() - datetime.timedelta(days=self.days)

        if self.id and not self.type:
            raise CommandError('Specifying id requires --type')

        n_aged_items = 0
        if not self.type:
            n_aged_items += self.cleanup_model(User)
            for model in self.get_models(PrimordialModel):
                n_aged_items += self.cleanup_model(model)
        else:
            model_found = None
            if self.type == User.__name__:
                model_found = User
            else:
                for model in self.get_models(PrimordialModel):
                    if model.__name__ == self.type:
                        model_found = model
                        break
                if not model_found:
                    raise RuntimeError("Invalid type %s" % self.type)
            n_aged_items += self.cleanup_model(model_found, self.id) 

        print("Aged %d items" % n_aged_items)

