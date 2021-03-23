from awxkit.api.resources import resources
from . import base
from . import page


class CredentialInputSource(base.Base):

    pass


page.register_page(resources.credential_input_source, CredentialInputSource)


class CredentialInputSources(page.PageList, CredentialInputSource):

    pass


page.register_page([resources.credential_input_sources, resources.related_input_sources], CredentialInputSources)
