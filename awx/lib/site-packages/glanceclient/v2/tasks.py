# Copyright 2013 OpenStack LLC.
# Copyright 2013 IBM Corp.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_utils import encodeutils
import six
import warlock

from glanceclient.common import utils
from glanceclient.v2 import schemas

DEFAULT_PAGE_SIZE = 20

SORT_DIR_VALUES = ('asc', 'desc')
SORT_KEY_VALUES = ('id', 'type', 'status')


class Controller(object):
    def __init__(self, http_client, schema_client):
        self.http_client = http_client
        self.schema_client = schema_client

    @utils.memoized_property
    def model(self):
        schema = self.schema_client.get('task')
        return warlock.model_factory(schema.raw(), schemas.SchemaBasedModel)

    def list(self, **kwargs):
        """Retrieve a listing of Task objects

        :param page_size: Number of tasks to request in each paginated request
        :returns generator over list of Tasks
        """
        def paginate(url):
            resp, body = self.http_client.get(url)
            for task in body['tasks']:
                yield task
            try:
                next_url = body['next']
            except KeyError:
                return
            else:
                for task in paginate(next_url):
                    yield task

        filters = kwargs.get('filters', {})

        if not kwargs.get('page_size'):
            filters['limit'] = DEFAULT_PAGE_SIZE
        else:
            filters['limit'] = kwargs['page_size']

        if 'marker' in kwargs:
            filters['marker'] = kwargs['marker']

        sort_key = kwargs.get('sort_key')
        if sort_key is not None:
            if sort_key in SORT_KEY_VALUES:
                filters['sort_key'] = sort_key
            else:
                raise ValueError('sort_key must be one of the following: %s.'
                                 % ', '.join(SORT_KEY_VALUES))

        sort_dir = kwargs.get('sort_dir')
        if sort_dir is not None:
            if sort_dir in SORT_DIR_VALUES:
                filters['sort_dir'] = sort_dir
            else:
                raise ValueError('sort_dir must be one of the following: %s.'
                                 % ', '.join(SORT_DIR_VALUES))

        for param, value in filters.items():
            if isinstance(value, six.string_types):
                filters[param] = encodeutils.safe_encode(value)

        url = '/v2/tasks?%s' % six.moves.urllib.parse.urlencode(filters)
        for task in paginate(url):
            #NOTE(flwang): remove 'self' for now until we have an elegant
            # way to pass it into the model constructor without conflict
            task.pop('self', None)
            yield self.model(**task)

    def get(self, task_id):
        """Get a task based on given task id."""
        url = '/v2/tasks/%s' % task_id
        resp, body = self.http_client.get(url)
        #NOTE(flwang): remove 'self' for now until we have an elegant
        # way to pass it into the model constructor without conflict
        body.pop('self', None)
        return self.model(**body)

    def create(self, **kwargs):
        """Create a new task."""
        url = '/v2/tasks'
        task = self.model()

        for (key, value) in kwargs.items():
            try:
                setattr(task, key, value)
            except warlock.InvalidOperation as e:
                raise TypeError(unicode(e))

        resp, body = self.http_client.post(url, data=task)
        #NOTE(flwang): remove 'self' for now until we have an elegant
        # way to pass it into the model constructor without conflict
        body.pop('self', None)
        return self.model(**body)
