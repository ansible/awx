from awxkit.api.resources import resources
from . import base
from . import page


class Instance(base.Base):
    pass


page.register_page(resources.instance, Instance)


class Instances(page.PageList, Instance):
    pass


page.register_page([resources.instances, resources.related_instances, resources.instance_peers], Instances)


class InstanceInstallBundle(page.Page):
    def extract_data(self, response):
        # The actual content of this response will be in the full set
        # of bytes from response.content, which will be exposed via
        # the Page.bytes interface.
        return {}


page.register_page(resources.instance_install_bundle, InstanceInstallBundle)
