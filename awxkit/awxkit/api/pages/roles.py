from awxkit.api.resources import resources
from . import base
from . import page


class Role(base.Base):

    pass


page.register_page(resources.role, Role)


class Roles(page.PageList, Role):

    pass


page.register_page([resources.roles,
                    resources.related_roles,
                    resources.related_object_roles], Roles)
