from awxkit.api.resources import resources
from . import base
from . import page


class Api(base.Base):

    pass


page.register_page(resources.api, Api)


class ApiV2(base.Base):

    pass


page.register_page(resources.v2, ApiV2)
