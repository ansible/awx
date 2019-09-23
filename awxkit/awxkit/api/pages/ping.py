from awxkit.api.resources import resources
from . import base
from . import page


class Ping(base.Base):

    pass


page.register_page(resources.ping, Ping)
