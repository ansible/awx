# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

from mongoengine.base import BaseField
from mongoengine import Document, DateTimeField, ReferenceField, StringField
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

    # TODO: Consider using hashed index on hostname. django-mongo may not support this but
    # executing raw js will
    meta = {
        'indexes': [
            'hostname' 
        ]
    }

    @staticmethod
    def get_host_id(hostname):
        host = FactHost.objects.get(hostname=hostname)
        if host:
            return host.id
        return None

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
            'host'
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
    def get_host_version(hostname, timestamp, module):
        try:
            host = FactHost.objects.get(hostname=hostname)
        except FactHost.DoesNotExist:
            return None

        kv = {
            'host' : host.id,
            'timestamp__lte': timestamp,
            'module': module,
        }

        try:
            facts = Fact.objects.filter(**kv)
            if not facts:
                return None
            return facts[0]
        except Fact.DoesNotExist:
            return None

    @staticmethod
    def get_host_timeline(hostname, module):
        try:
            host = FactHost.objects.get(hostname=hostname)
        except FactHost.DoesNotExist:
            return None

        kv = {
            'host': host.id,
            'module': module,
        }

        return FactVersion.objects.filter(**kv).values_list('timestamp')

    @staticmethod
    def get_single_facts(hostnames, fact_key, timestamp, module):
        host_ids = FactHost.objects.filter(hostname__in=hostnames).values_list('id')
        if not host_ids or len(host_ids) == 0:
            return None

        kv = {
            'host__in': host_ids,
            'timestamp__lte': timestamp,
            'module': module,
        }
        facts = FactVersion.objects.filter(**kv).values_list('fact')
        if not facts or len(facts) == 0:
            return None
        # TODO: Make sure the below doesn't trigger a query to get the fact record
        # It's unclear as to if mongoengine will query the full fact when the id is referenced.
        # This is not a logic problem, but a performance problem.
        fact_ids = [fact.id for fact in facts]

        project = {
            '$project': {
                'host': 1,
                'fact.%s' % fact_key: 1,
            }
        }
        facts = Fact.objects.filter(id__in=fact_ids).aggregate(project)
        return facts


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
            'module'
        ]
    }
    