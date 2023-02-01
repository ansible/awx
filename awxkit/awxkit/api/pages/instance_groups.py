from contextlib import suppress

from awxkit.utils import PseudoNamespace, random_title, update_payload, set_payload_foreign_key_args
from awxkit.api.resources import resources
from awxkit.api.mixins import HasCreate
import awxkit.exceptions as exc
from . import base
from . import page


class InstanceGroup(HasCreate, base.Base):
    def add_instance(self, instance):
        with suppress(exc.NoContent):
            self.related.instances.post(dict(id=instance.id))

    def remove_instance(self, instance):
        with suppress(exc.NoContent):
            self.related.instances.post(dict(id=instance.id, disassociate=True))

    def payload(self, **kwargs):
        payload = PseudoNamespace(name=kwargs.get('name') or 'Instance Group - {}'.format(random_title()))
        fields = ('policy_instance_percentage', 'policy_instance_minimum', 'policy_instance_list', 'is_container_group', 'max_forks', 'max_concurrent_jobs')
        update_payload(payload, fields, kwargs)

        set_payload_foreign_key_args(payload, ('credential',), kwargs)

        return payload

    def create_payload(self, name='', **kwargs):
        payload = self.payload(name=name, **kwargs)
        return payload

    def create(self, name='', **kwargs):
        payload = self.create_payload(name=name, **kwargs)
        return self.update_identity(InstanceGroups(self.connection).post(payload))


page.register_page([resources.instance_group, (resources.instance_groups, 'post')], InstanceGroup)


class InstanceGroups(page.PageList, InstanceGroup):
    pass


page.register_page([resources.instance_groups, resources.related_instance_groups], InstanceGroups)
