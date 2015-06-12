# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

from mongoengine.base import BaseField
from mongoengine import Document, DateTimeField, ReferenceField, StringField, IntField
from awx.fact.utils.dbtransform import KeyTransform

key_transform = KeyTransform([('.', '\uff0E'), ('$', '\uff04')])

class TransformField(BaseField):
    def to_python(self, value):
        return key_transform.transform_outgoing(value, None)

    def prepare_query_value(self, op, value):
        if op == 'set':
            value = key_transform.transform_incoming(value, None)
        return super(TransformField, self).prepare_query_value(op, value)

    def to_mongo(self, value):
        value = key_transform.transform_incoming(value, None)
        return value

class FactHost(Document):
    hostname = StringField(max_length=100, required=True, unique=True)
    inventory_id = IntField(required=True)

    # TODO: Consider using hashed index on hostname. django-mongo may not support this but
    # executing raw js will
    meta = {
        'indexes': [
            'hostname',
            'inventory_id'
        ]
    }

class Fact(Document):
    timestamp = DateTimeField(required=True)
    host = ReferenceField(FactHost, required=True)
    module = StringField(max_length=50, required=True)
    fact = TransformField(required=True)

    # TODO: Consider using hashed index on host. django-mongo may not support this but
    # executing raw js will
    meta = {
        'indexes': [
            '-timestamp',
            'host',
        ]
    }

    @staticmethod
    def add_fact(timestamp, fact, host, module):
        fact_obj = Fact(timestamp=timestamp, host=host, module=module, fact=fact)
        fact_obj.save()
        version_obj = FactVersion(timestamp=timestamp, host=host, module=module, fact=fact_obj)
        version_obj.save()
        return (fact_obj, version_obj)

    # TODO: if we want to relax the need to include module...
    # If module not specified then filter query may return more than 1 result.
    # Thus, the resulting facts must somehow be unioned/concated/ or kept as an array.
    @staticmethod
    def get_host_version(hostname, inventory_id, timestamp, module):
        try:
            host = FactHost.objects.get(hostname=hostname, inventory_id=inventory_id)
        except FactHost.DoesNotExist:
            return None

        kv = {
            'host' : host.id,
            'timestamp__lte': timestamp,
            'module': module,
        }

        try:
            facts = Fact.objects.filter(**kv).order_by("-timestamp")
            if not facts:
                return None
            return facts[0]
        except Fact.DoesNotExist:
            return None

    @staticmethod
    def get_host_timeline(hostname, inventory_id, module):
        try:
            host = FactHost.objects.get(hostname=hostname, inventory_id=inventory_id)
        except FactHost.DoesNotExist:
            return None

        kv = {
            'host': host.id,
            'module': module,
        }

        return FactVersion.objects.filter(**kv).order_by("-timestamp").values_list('timestamp')

    # FIXME: single facts no longer works with the addition of the inventory_id field to the FactHost document
    @staticmethod
    def get_single_facts(hostnames, fact_key, fact_value, timestamp, module):
        kv = {
            'hostname': {
                '$in': hostnames,
            }
        }
        fields = {
            '_id': 1
        }
        host_ids = FactHost._get_collection().find(kv, fields)
        if not host_ids or host_ids.count() == 0:
            return None
        # TODO: use mongo to transform [{_id: <>}, {_id: <>},...] into [_id, _id,...]
        host_ids = [e['_id'] for e in host_ids]

        pipeline = []
        match = {
            'host': {
                '$in': host_ids
            },
            'timestamp': {
                '$lte': timestamp
            },
            'module': module
        }
        sort = {
            'timestamp': -1
        }
        group = {
            '_id': '$host',
            'timestamp': {
                '$first': '$timestamp'
            },
            'fact': {
                '$first': '$fact'
            }
        }
        project = {
            '_id': 0,
            'fact': 1,
        }
        pipeline.append({'$match': match}) # noqa
        pipeline.append({'$sort': sort}) # noqa
        pipeline.append({'$group': group}) # noqa
        pipeline.append({'$project': project}) # noqa
        q = FactVersion._get_collection().aggregate(pipeline)
        if not q or 'result' not in q or len(q['result']) == 0:
            return None
        # TODO: use mongo to transform [{fact: <>}, {fact: <>},...] into [fact, fact,...]
        fact_ids = [fact['fact'] for fact in q['result']]

        kv = {
            'fact.%s' % fact_key : fact_value,
            '_id': {
                '$in': fact_ids
            }
        }
        fields = {
            'fact.%s.$' % fact_key : 1,
            'host': 1,
            'timestamp': 1,
            'module': 1,
        }
        facts = Fact._get_collection().find(kv, fields)
        #fact_objs = [Fact(**f) for f in facts]
        # Translate pymongo python structure to mongoengine Fact object
        fact_objs = []
        for f in facts:
            f['id'] = f.pop('_id')
            fact_objs.append(Fact(**f))
        return fact_objs

class FactVersion(Document):
    timestamp = DateTimeField(required=True)
    host = ReferenceField(FactHost, required=True)
    module = StringField(max_length=50, required=True)
    fact = ReferenceField(Fact, required=True)
    # TODO: Consider using hashed index on module. django-mongo may not support this but
    # executing raw js will
    meta = {
        'indexes': [
            '-timestamp',
            'module',
            'host',
        ]
    }
