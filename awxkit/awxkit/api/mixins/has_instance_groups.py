from awxkit.utils import suppress
import awxkit.exceptions as exc


class HasInstanceGroups(object):

    def add_instance_group(self, instance_group):
        with suppress(exc.NoContent):
            self.related['instance_groups'].post(dict(id=instance_group.id))

    def remove_instance_group(self, instance_group):
        with suppress(exc.NoContent):
            self.related['instance_groups'].post(dict(id=instance_group.id, disassociate=instance_group.id))

    def remove_all_instance_groups(self):
        for ig in self.related.instance_groups.get().results:
            self.remove_instance_group(ig)
