from awxkit.api.resources import resources
from . import page


class Subscriptions(page.Page):

    def get_possible_licenses(self, **kwargs):
        return self.post(json=kwargs).json

    def attach(self, **kwargs):
        return self.connection.post(resources.subscriptions_attach, json=kwargs).json


page.register_page(resources.subscriptions, Subscriptions)
