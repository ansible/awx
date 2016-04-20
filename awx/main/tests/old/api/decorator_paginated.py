# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

import json

from django.test import TestCase

from rest_framework.permissions import AllowAny
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from awx.api.utils.decorators import paginated


class PaginatedDecoratorTests(TestCase):
    """A set of tests for ensuring that the "paginated" decorator works
    in the way we expect.
    """
    def setUp(self):
        self.rf = APIRequestFactory()

        # Define an uninteresting view that we can use to test
        # that the paginator wraps in the way we expect.
        class View(APIView):
            permission_classes = (AllowAny,)

            @paginated
            def get(self, request, limit, ordering, offset):
                return ['a', 'b', 'c', 'd', 'e'], 26, None
        self.view = View.as_view()

    def test_implicit_first_page(self):
        """Establish that if we get an implicit request for the first page
        (e.g. no page provided), that it is returned appropriately.
        """
        # Create a request, and run the paginated function.
        request = self.rf.get('/dummy/', {'page_size': 5})
        response = self.view(request)

        # Ensure the response looks like what it should.
        r = json.loads(response.rendered_content)
        self.assertEqual(r['count'], 26)
        self.assertEqual(r['next'], '/dummy/?page=2&page_size=5')
        self.assertEqual(r['previous'], None)
        self.assertEqual(r['results'], ['a', 'b', 'c', 'd', 'e'])

    def test_mid_page(self):
        """Establish that if we get a request for a page in the middle, that
        the paginator causes next and prev to be set appropriately.
        """
        # Create a request, and run the paginated function.
        request = self.rf.get('/dummy/', {'page': 3, 'page_size': 5})
        response = self.view(request)

        # Ensure the response looks like what it should.
        r = json.loads(response.rendered_content)
        self.assertEqual(r['count'], 26)
        self.assertEqual(r['next'], '/dummy/?page=4&page_size=5')
        self.assertEqual(r['previous'], '/dummy/?page=2&page_size=5')
        self.assertEqual(r['results'], ['a', 'b', 'c', 'd', 'e'])

    def test_last_page(self):
        """Establish that if we get a request for the last page, that the
        paginator picks up on it and sets `next` to None.
        """
        # Create a request, and run the paginated function.
        request = self.rf.get('/dummy/', {'page': 6, 'page_size': 5})
        response = self.view(request)

        # Ensure the response looks like what it should.
        r = json.loads(response.rendered_content)
        self.assertEqual(r['count'], 26)
        self.assertEqual(r['next'], None)
        self.assertEqual(r['previous'], '/dummy/?page=5&page_size=5')
        self.assertEqual(r['results'], ['a', 'b', 'c', 'd', 'e'])
