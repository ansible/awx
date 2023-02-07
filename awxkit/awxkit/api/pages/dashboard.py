from awxkit.api.resources import resources
from . import base
from . import page


class Dashboard(base.Base):
    pass


page.register_page(resources.dashboard, Dashboard)
