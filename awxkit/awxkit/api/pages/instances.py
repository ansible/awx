from awxkit.api.resources import resources
from . import base
from . import page


class Instance(base.Base):

    pass


page.register_page(resources.instance, Instance)


class Instances(page.PageList, Instance):

    pass


page.register_page([resources.instances,
                    resources.related_instances], Instances)
