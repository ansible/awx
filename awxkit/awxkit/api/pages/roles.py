from awxkit.api.resources import resources
import awxkit.exceptions as exc

from . import base
from . import page


class Role(base.Base):

    NATURAL_KEY = ('name',)

    def get_natural_key(self):
        natural_key = super(Role, self).get_natural_key()
        related_objs = [
            related for name, related in self.related.items()
            if name not in ('users', 'teams')
        ]
        if related_objs:
            try:
                # FIXME: use caching by url
                natural_key['content_object'] = related_objs[0].get().get_natural_key()
            except exc.Forbidden:
                return None

        return natural_key


page.register_page(resources.role, Role)


class Roles(page.PageList, Role):

    pass


page.register_page([resources.roles,
                    resources.related_roles,
                    resources.related_object_roles], Roles)
