import logging

from awxkit.api.resources import resources

from . import base
from . import page


log = logging.getLogger(__name__)


class Role(base.Base):
    NATURAL_KEY = ('name',)

    def get_natural_key(self, cache=None):
        if cache is None:
            cache = page.PageCache()

        natural_key = super(Role, self).get_natural_key(cache=cache)
        related_objs = [related for name, related in self.related.items() if name not in ('users', 'teams')]
        if related_objs:
            related_endpoint = cache.get_page(related_objs[0])
            if related_endpoint is None:
                log.error("Unable to obtain content_object %s for role %s", related_objs[0], self.endpoint)
                return None
            natural_key['content_object'] = related_endpoint.get_natural_key(cache=cache)

        return natural_key


page.register_page(resources.role, Role)


class Roles(page.PageList, Role):
    pass


page.register_page([resources.roles, resources.related_roles, resources.related_object_roles], Roles)
