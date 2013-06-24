# encoding: utf-8
from __future__ import absolute_import

import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models
from django.db import DatabaseError


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Adding model 'TaskMeta'
        db.create_table('celery_taskmeta', (
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('task_id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
                ('status', self.gf('django.db.models.fields.CharField')(default='PENDING', max_length=50)),
                ('result', self.gf('djcelery.picklefield.PickledObjectField')(default=None, null=True)),
                ('date_done', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
                ('traceback', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),))
        db.send_create_signal('djcelery', ['TaskMeta'])

        # Adding model 'TaskSetMeta'
        db.create_table('celery_tasksetmeta', (
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('taskset_id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
                ('result', self.gf('djcelery.picklefield.PickledObjectField')()),
                ('date_done', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),))
        db.send_create_signal('djcelery', ['TaskSetMeta'])

        # Adding model 'IntervalSchedule'
        db.create_table('djcelery_intervalschedule', (
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('every', self.gf('django.db.models.fields.IntegerField')()),
                ('period', self.gf('django.db.models.fields.CharField')(max_length=24)),))
        db.send_create_signal('djcelery', ['IntervalSchedule'])

        # Adding model 'CrontabSchedule'
        db.create_table('djcelery_crontabschedule', (
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('minute', self.gf('django.db.models.fields.CharField')(default='*', max_length=64)),
                ('hour', self.gf('django.db.models.fields.CharField')(default='*', max_length=64)),
                ('day_of_week', self.gf('django.db.models.fields.CharField')(default='*', max_length=64)),))
        db.send_create_signal('djcelery', ['CrontabSchedule'])

        # Adding model 'PeriodicTasks'
        db.create_table('djcelery_periodictasks', (
                ('ident', self.gf('django.db.models.fields.SmallIntegerField')(default=1, unique=True, primary_key=True)),
                ('last_update', self.gf('django.db.models.fields.DateTimeField')()),))
        db.send_create_signal('djcelery', ['PeriodicTasks'])

        # Adding model 'PeriodicTask'
        db.create_table('djcelery_periodictask', (
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=200)),
                ('task', self.gf('django.db.models.fields.CharField')(max_length=200)),
                ('interval', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['djcelery.IntervalSchedule'], null=True, blank=True)),
                ('crontab', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['djcelery.CrontabSchedule'], null=True, blank=True)),
                ('args', self.gf('django.db.models.fields.TextField')(default='[]', blank=True)),
                ('kwargs', self.gf('django.db.models.fields.TextField')(default='{}', blank=True)),
                ('queue', self.gf('django.db.models.fields.CharField')(default=None, max_length=200, null=True, blank=True)),
                ('exchange', self.gf('django.db.models.fields.CharField')(default=None, max_length=200, null=True, blank=True)),
                ('routing_key', self.gf('django.db.models.fields.CharField')(default=None, max_length=200, null=True, blank=True)),
                ('expires', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
                ('enabled', self.gf('django.db.models.fields.BooleanField')(default=True)),
                ('last_run_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
                ('total_run_count', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
                ('date_changed', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),))
        db.send_create_signal('djcelery', ['PeriodicTask'])

        # Adding model 'WorkerState'
        db.create_table('djcelery_workerstate', (
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('hostname', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
                ('last_heartbeat', self.gf('django.db.models.fields.DateTimeField')(null=True, db_index=True)),))
        db.send_create_signal('djcelery', ['WorkerState'])

        # Adding model 'TaskState'
        db.create_table('djcelery_taskstate', (
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('state', self.gf('django.db.models.fields.CharField')(max_length=64, db_index=True)),
                ('task_id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=36)),
                ('name', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, db_index=True)),
                ('tstamp', self.gf('django.db.models.fields.DateTimeField')(db_index=True)),
                ('args', self.gf('django.db.models.fields.TextField')(null=True)),
                ('kwargs', self.gf('django.db.models.fields.TextField')(null=True)),
                ('eta', self.gf('django.db.models.fields.DateTimeField')(null=True)),
                ('expires', self.gf('django.db.models.fields.DateTimeField')(null=True)),
                ('result', self.gf('django.db.models.fields.TextField')(null=True)),
                ('traceback', self.gf('django.db.models.fields.TextField')(null=True)),
                ('runtime', self.gf('django.db.models.fields.FloatField')(null=True)),
                ('retries', self.gf('django.db.models.fields.IntegerField')(default=0)),
                ('worker', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['djcelery.WorkerState'], null=True)),
                ('hidden', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True)),))
        db.send_create_signal('djcelery', ['TaskState'])


    def backwards(self, orm):

        # Deleting model 'TaskMeta'
        db.delete_table('celery_taskmeta')

        # Deleting model 'TaskSetMeta'
        db.delete_table('celery_tasksetmeta')

        # Deleting model 'IntervalSchedule'
        db.delete_table('djcelery_intervalschedule')

        # Deleting model 'CrontabSchedule'
        db.delete_table('djcelery_crontabschedule')

        # Deleting model 'PeriodicTasks'
        db.delete_table('djcelery_periodictasks')

        # Deleting model 'PeriodicTask'
        db.delete_table('djcelery_periodictask')

        # Deleting model 'WorkerState'
        db.delete_table('djcelery_workerstate')

        # Deleting model 'TaskState'
        db.delete_table('djcelery_taskstate')


    models = {
        'djcelery.crontabschedule': {
            'Meta': {'object_name': 'CrontabSchedule'},
            'day_of_week': ('django.db.models.fields.CharField', [], {'default': "'*'", 'max_length': '64'}),
            'hour': ('django.db.models.fields.CharField', [], {'default': "'*'", 'max_length': '64'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'minute': ('django.db.models.fields.CharField', [], {'default': "'*'", 'max_length': '64'})
        },
        'djcelery.intervalschedule': {
            'Meta': {'object_name': 'IntervalSchedule'},
            'every': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'period': ('django.db.models.fields.CharField', [], {'max_length': '24'})
        },
        'djcelery.periodictask': {
            'Meta': {'object_name': 'PeriodicTask'},
            'args': ('django.db.models.fields.TextField', [], {'default': "'[]'", 'blank': 'True'}),
            'crontab': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['djcelery.CrontabSchedule']", 'null': 'True', 'blank': 'True'}),
            'date_changed': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'exchange': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'expires': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interval': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['djcelery.IntervalSchedule']", 'null': 'True', 'blank': 'True'}),
            'kwargs': ('django.db.models.fields.TextField', [], {'default': "'{}'", 'blank': 'True'}),
            'last_run_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'queue': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'routing_key': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'task': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'total_run_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        },
        'djcelery.periodictasks': {
            'Meta': {'object_name': 'PeriodicTasks'},
            'ident': ('django.db.models.fields.SmallIntegerField', [], {'default': '1', 'unique': 'True', 'primary_key': 'True'}),
            'last_update': ('django.db.models.fields.DateTimeField', [], {})
        },
        'djcelery.taskmeta': {
            'Meta': {'object_name': 'TaskMeta', 'db_table': "'celery_taskmeta'"},
            'date_done': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'result': ('djcelery.picklefield.PickledObjectField', [], {'default': 'None', 'null': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'PENDING'", 'max_length': '50'}),
            'task_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'traceback': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        },
        'djcelery.tasksetmeta': {
            'Meta': {'object_name': 'TaskSetMeta', 'db_table': "'celery_tasksetmeta'"},
            'date_done': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'result': ('djcelery.picklefield.PickledObjectField', [], {}),
            'taskset_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        'djcelery.taskstate': {
            'Meta': {'ordering': "['-tstamp']", 'object_name': 'TaskState'},
            'args': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'eta': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'expires': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kwargs': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'db_index': 'True'}),
            'result': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'retries': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'runtime': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '64', 'db_index': 'True'}),
            'task_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '36'}),
            'traceback': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'tstamp': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'worker': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['djcelery.WorkerState']", 'null': 'True'})
        },
        'djcelery.workerstate': {
            'Meta': {'ordering': "['-last_heartbeat']", 'object_name': 'WorkerState'},
            'hostname': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_heartbeat': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'})
        }
    }

    complete_apps = ['djcelery']
