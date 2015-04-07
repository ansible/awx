# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from keystoneclient import base
from keystoneclient.v3.contrib.oauth1 import utils


class Consumer(base.Resource):
    """Represents an OAuth consumer.

    Attributes:
        * id: a uuid that identifies the consumer
        * description: a short description of the consumer
    """
    pass


class ConsumerManager(base.CrudManager):
    """Manager class for manipulating identity consumers."""
    resource_class = Consumer
    collection_key = 'consumers'
    key = 'consumer'
    base_url = utils.OAUTH_PATH

    def create(self, description=None, **kwargs):
        return super(ConsumerManager, self).create(
            description=description,
            **kwargs)

    def get(self, consumer):
        return super(ConsumerManager, self).get(
            consumer_id=base.getid(consumer))

    def update(self, consumer, description=None, **kwargs):
        return super(ConsumerManager, self).update(
            consumer_id=base.getid(consumer),
            description=description,
            **kwargs)

    def delete(self, consumer):
        return super(ConsumerManager, self).delete(
            consumer_id=base.getid(consumer))
