from awxkit.api.resources import resources
from . import base
from . import page


class ActivityStream(base.Base):

    pass


page.register_page(resources.activity, ActivityStream)


class ActivityStreams(page.PageList, ActivityStream):

    pass


page.register_page([resources.activity_stream, resources.object_activity_stream], ActivityStreams)
