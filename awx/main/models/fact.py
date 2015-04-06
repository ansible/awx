from mongoengine import Document, DynamicDocument, DateTimeField, ReferenceField, StringField

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

class Fact(DynamicDocument):
    timestamp = DateTimeField(required=True)
    host = ReferenceField(FactHost, required=True)
    module = StringField(max_length=50, required=True)
    # fact = <anything>

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

    @staticmethod
    def get_version(hostname, timestamp, module=None):
        try:
            host = FactHost.objects.get(hostname=hostname)
        except FactHost.DoesNotExist:
            return None

        kv = {
            'host' : host.id,
            'timestamp__lte': timestamp
        }
        if module:
            kv['module'] = module

        try:
            facts = Fact.objects.filter(**kv)
            if not facts:
                return None
            return facts[0]
        except Fact.DoesNotExist:
            return None

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