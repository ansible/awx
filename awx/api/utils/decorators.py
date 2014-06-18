# Copyright (c) 2014 Ansible, Inc.
# All Rights Reserved.

import collections
import copy
import functools

from rest_framework.response import Response
from rest_framework.settings import api_settings

def paginated(method):
    """Given an method with a Django REST Framework API method signature
    (e.g. `def get(self, request, ...):`), abstract out boilerplate pagination
    duties.

    This causes the method to receive two additional keyword arguments:
    `limit`, and `offset`. The method expects a two-tuple to be
    returned, with a result list as the first item, and the total number
    of results (across all pages) as the second item.
    """
    @functools.wraps(method)
    def func(self, request, *args, **kwargs):
        # Manually spin up pagination.
        # How many results do we show?
        limit = api_settings.PAGINATE_BY
        if request.QUERY_PARAMS.get(api_settings.PAGINATE_BY_PARAM, False):
            limit = request.QUERY_PARAMS[api_settings.PAGINATE_BY_PARAM]
        if api_settings.MAX_PAGINATE_BY:
            limit = min(api_settings.MAX_PAGINATE_BY, limit)
        limit = int(limit)

        # What page are we on?
        page = int(request.QUERY_PARAMS.get('page', 1))
        offset = (page - 1) * limit

        # Add the limit, offset, and page variables to the keyword arguments
        # being sent to the underlying method.
        kwargs['limit'] = limit
        kwargs['offset'] = offset

        # Okay, call the underlying method.
        results, count = method(self, request, *args, **kwargs)

        # Determine the next and previous pages, if any.
        prev, next_ = None, None
        if page > 1:
            get_copy = copy.copy(request.GET)
            get_copy['page'] = page - 1
            prev = '%s?%s' % (request.path, get_copy.urlencode())
        if count > offset + limit:
            get_copy = copy.copy(request.GET)
            get_copy['page'] = page + 1
            next_ = '%s?%s' % (request.path, get_copy.urlencode())

        # Compile the results into a dictionary with pagination
        # information.
        answer = collections.OrderedDict((
            ('count', count),
            ('next', next_),
            ('previous', prev),
            ('results', results),
        ))

        # Okay, we're done; return response data.
        return Response(answer)
    return func
