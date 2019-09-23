from awxkit.api.resources import resources
from . import base
from . import page


class AuthToken(base.Base):

    pass


page.register_page(resources.authtoken, AuthToken)
