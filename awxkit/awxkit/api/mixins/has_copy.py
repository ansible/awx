from awxkit.api.pages import Page
from awxkit.utils import random_title


class HasCopy(object):
    def can_copy(self):
        return self.get_related('copy').can_copy

    def copy(self, name=''):
        """Return a copy of current page"""
        payload = {"name": name or "Copy - " + random_title()}
        endpoint = self.json.related['copy']
        page = Page(self.connection, endpoint=endpoint)
        return page.post(payload)
