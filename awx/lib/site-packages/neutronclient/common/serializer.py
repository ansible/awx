# Copyright 2013 OpenStack Foundation.
# All Rights Reserved
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
#
###
### Codes from neutron wsgi
###

import logging
from xml.etree import ElementTree as etree
from xml.parsers import expat

from oslo.serialization import jsonutils
import six

from neutronclient.common import constants
from neutronclient.common import exceptions as exception
from neutronclient.i18n import _

LOG = logging.getLogger(__name__)

if six.PY3:
    long = int


class ActionDispatcher(object):
    """Maps method name to local methods through action name."""

    def dispatch(self, *args, **kwargs):
        """Find and call local method."""
        action = kwargs.pop('action', 'default')
        action_method = getattr(self, str(action), self.default)
        return action_method(*args, **kwargs)

    def default(self, data):
        raise NotImplementedError()


class DictSerializer(ActionDispatcher):
    """Default request body serialization."""

    def serialize(self, data, action='default'):
        return self.dispatch(data, action=action)

    def default(self, data):
        return ""


class JSONDictSerializer(DictSerializer):
    """Default JSON request body serialization."""

    def default(self, data):
        def sanitizer(obj):
            return six.text_type(obj)
        return jsonutils.dumps(data, default=sanitizer)


class XMLDictSerializer(DictSerializer):

    def __init__(self, metadata=None, xmlns=None):
        """XMLDictSerializer constructor.

        :param metadata: information needed to deserialize XML into
                         a dictionary.
        :param xmlns: XML namespace to include with serialized XML
        """
        super(XMLDictSerializer, self).__init__()
        self.metadata = metadata or {}
        if not xmlns:
            xmlns = self.metadata.get('xmlns')
        if not xmlns:
            xmlns = constants.XML_NS_V20
        self.xmlns = xmlns

    def default(self, data):
        """Default serializer of XMLDictSerializer.

        :param data: expect data to contain a single key as XML root, or
                     contain another '*_links' key as atom links. Other
                     case will use 'VIRTUAL_ROOT_KEY' as XML root.
        """
        try:
            links = None
            has_atom = False
            if data is None:
                root_key = constants.VIRTUAL_ROOT_KEY
                root_value = None
            else:
                link_keys = [k for k in six.iterkeys(data) or []
                             if k.endswith('_links')]
                if link_keys:
                    links = data.pop(link_keys[0], None)
                    has_atom = True
                root_key = (len(data) == 1 and
                            list(data.keys())[0] or constants.VIRTUAL_ROOT_KEY)
                root_value = data.get(root_key, data)
            doc = etree.Element("_temp_root")
            used_prefixes = []
            self._to_xml_node(doc, self.metadata, root_key,
                              root_value, used_prefixes)
            if links:
                self._create_link_nodes(list(doc)[0], links)
            return self.to_xml_string(list(doc)[0], used_prefixes, has_atom)
        except AttributeError as e:
            LOG.exception(str(e))
            return ''

    def __call__(self, data):
        # Provides a migration path to a cleaner WSGI layer, this
        # "default" stuff and extreme extensibility isn't being used
        # like originally intended
        return self.default(data)

    def to_xml_string(self, node, used_prefixes, has_atom=False):
        self._add_xmlns(node, used_prefixes, has_atom)
        return etree.tostring(node, encoding='UTF-8')

    #NOTE (ameade): the has_atom should be removed after all of the
    # XML serializers and view builders have been updated to the current
    # spec that required all responses include the xmlns:atom, the has_atom
    # flag is to prevent current tests from breaking
    def _add_xmlns(self, node, used_prefixes, has_atom=False):
        node.set('xmlns', self.xmlns)
        node.set(constants.TYPE_XMLNS, self.xmlns)
        if has_atom:
            node.set(constants.ATOM_XMLNS, constants.ATOM_NAMESPACE)
        node.set(constants.XSI_NIL_ATTR, constants.XSI_NAMESPACE)
        ext_ns = self.metadata.get(constants.EXT_NS, {})
        for prefix in used_prefixes:
            if prefix in ext_ns:
                node.set('xmlns:' + prefix, ext_ns[prefix])

    def _to_xml_node(self, parent, metadata, nodename, data, used_prefixes):
        """Recursive method to convert data members to XML nodes."""
        result = etree.SubElement(parent, nodename)
        if ":" in nodename:
            used_prefixes.append(nodename.split(":", 1)[0])
        #TODO(bcwaldon): accomplish this without a type-check
        if isinstance(data, list):
            if not data:
                result.set(
                    constants.TYPE_ATTR,
                    constants.TYPE_LIST)
                return result
            singular = metadata.get('plurals', {}).get(nodename, None)
            if singular is None:
                if nodename.endswith('s'):
                    singular = nodename[:-1]
                else:
                    singular = 'item'
            for item in data:
                self._to_xml_node(result, metadata, singular, item,
                                  used_prefixes)
        #TODO(bcwaldon): accomplish this without a type-check
        elif isinstance(data, dict):
            if not data:
                result.set(
                    constants.TYPE_ATTR,
                    constants.TYPE_DICT)
                return result
            attrs = metadata.get('attributes', {}).get(nodename, {})
            for k, v in sorted(data.items()):
                if k in attrs:
                    result.set(k, str(v))
                else:
                    self._to_xml_node(result, metadata, k, v,
                                      used_prefixes)
        elif data is None:
            result.set(constants.XSI_ATTR, 'true')
        else:
            if isinstance(data, bool):
                result.set(
                    constants.TYPE_ATTR,
                    constants.TYPE_BOOL)
            elif isinstance(data, int):
                result.set(
                    constants.TYPE_ATTR,
                    constants.TYPE_INT)
            elif isinstance(data, long):
                result.set(
                    constants.TYPE_ATTR,
                    constants.TYPE_LONG)
            elif isinstance(data, float):
                result.set(
                    constants.TYPE_ATTR,
                    constants.TYPE_FLOAT)
            LOG.debug("Data %(data)s type is %(type)s",
                      {'data': data,
                       'type': type(data)})
            result.text = six.text_type(data)
        return result

    def _create_link_nodes(self, xml_doc, links):
        for link in links:
            link_node = etree.SubElement(xml_doc, 'atom:link')
            link_node.set('rel', link['rel'])
            link_node.set('href', link['href'])


class TextDeserializer(ActionDispatcher):
    """Default request body deserialization."""

    def deserialize(self, datastring, action='default'):
        return self.dispatch(datastring, action=action)

    def default(self, datastring):
        return {}


class JSONDeserializer(TextDeserializer):

    def _from_json(self, datastring):
        try:
            return jsonutils.loads(datastring)
        except ValueError:
            msg = _("Cannot understand JSON")
            raise exception.MalformedResponseBody(reason=msg)

    def default(self, datastring):
        return {'body': self._from_json(datastring)}


class XMLDeserializer(TextDeserializer):

    def __init__(self, metadata=None):
        """XMLDeserializer constructor.

        :param metadata: information needed to deserialize XML into
                         a dictionary.
        """
        super(XMLDeserializer, self).__init__()
        self.metadata = metadata or {}
        xmlns = self.metadata.get('xmlns')
        if not xmlns:
            xmlns = constants.XML_NS_V20
        self.xmlns = xmlns

    def _get_key(self, tag):
        tags = tag.split("}", 1)
        if len(tags) == 2:
            ns = tags[0][1:]
            bare_tag = tags[1]
            ext_ns = self.metadata.get(constants.EXT_NS, {})
            if ns == self.xmlns:
                return bare_tag
            for prefix, _ns in ext_ns.items():
                if ns == _ns:
                    return prefix + ":" + bare_tag
        else:
            return tag

    def _get_links(self, root_tag, node):
        link_nodes = node.findall(constants.ATOM_LINK_NOTATION)
        root_tag = self._get_key(node.tag)
        link_key = "%s_links" % root_tag
        link_list = []
        for link in link_nodes:
            link_list.append({'rel': link.get('rel'),
                              'href': link.get('href')})
            # Remove link node in order to avoid link node being
            # processed as an item in _from_xml_node
            node.remove(link)
        return link_list and {link_key: link_list} or {}

    def _from_xml(self, datastring):
        if datastring is None:
            return None
        plurals = set(self.metadata.get('plurals', {}))
        try:
            node = etree.fromstring(datastring)
            root_tag = self._get_key(node.tag)
            links = self._get_links(root_tag, node)
            result = self._from_xml_node(node, plurals)
            # There is no case where root_tag = constants.VIRTUAL_ROOT_KEY
            # and links is not None because of the way data are serialized
            if root_tag == constants.VIRTUAL_ROOT_KEY:
                return result
            return dict({root_tag: result}, **links)
        except Exception as e:
            parseError = False
            # Python2.7
            if (hasattr(etree, 'ParseError') and
                    isinstance(e, getattr(etree, 'ParseError'))):
                parseError = True
            # Python2.6
            elif isinstance(e, expat.ExpatError):
                parseError = True
            if parseError:
                msg = _("Cannot understand XML")
                raise exception.MalformedResponseBody(reason=msg)
            else:
                raise

    def _from_xml_node(self, node, listnames):
        """Convert a minidom node to a simple Python type.

        :param node: minidom node name
        :param listnames: list of XML node names whose subnodes should
                          be considered list items.

        """
        attrNil = node.get(str(etree.QName(constants.XSI_NAMESPACE, "nil")))
        attrType = node.get(str(etree.QName(
            self.metadata.get('xmlns'), "type")))
        if (attrNil and attrNil.lower() == 'true'):
            return None
        elif not len(node) and not node.text:
            if (attrType and attrType == constants.TYPE_DICT):
                return {}
            elif (attrType and attrType == constants.TYPE_LIST):
                return []
            else:
                return ''
        elif (len(node) == 0 and node.text):
            converters = {constants.TYPE_BOOL:
                          lambda x: x.lower() == 'true',
                          constants.TYPE_INT:
                          lambda x: int(x),
                          constants.TYPE_LONG:
                          lambda x: long(x),
                          constants.TYPE_FLOAT:
                          lambda x: float(x)}
            if attrType and attrType in converters:
                return converters[attrType](node.text)
            else:
                return node.text
        elif self._get_key(node.tag) in listnames:
            return [self._from_xml_node(n, listnames) for n in node]
        else:
            result = dict()
            for attr in node.keys():
                if (attr == 'xmlns' or
                        attr.startswith('xmlns:') or
                        attr == constants.XSI_ATTR or
                        attr == constants.TYPE_ATTR):
                    continue
                result[self._get_key(attr)] = node.get(attr)
            children = list(node)
            for child in children:
                result[self._get_key(child.tag)] = self._from_xml_node(
                    child, listnames)
            return result

    def default(self, datastring):
        return {'body': self._from_xml(datastring)}

    def __call__(self, datastring):
        # Adding a migration path to allow us to remove unncessary classes
        return self.default(datastring)


# NOTE(maru): this class is duplicated from neutron.wsgi
class Serializer(object):
    """Serializes and deserializes dictionaries to certain MIME types."""

    def __init__(self, metadata=None, default_xmlns=None):
        """Create a serializer based on the given WSGI environment.

        'metadata' is an optional dict mapping MIME types to information
        needed to serialize a dictionary to that type.

        """
        self.metadata = metadata or {}
        self.default_xmlns = default_xmlns

    def _get_serialize_handler(self, content_type):
        handlers = {
            'application/json': JSONDictSerializer(),
            'application/xml': XMLDictSerializer(self.metadata),
        }

        try:
            return handlers[content_type]
        except Exception:
            raise exception.InvalidContentType(content_type=content_type)

    def serialize(self, data, content_type):
        """Serialize a dictionary into the specified content type."""
        return self._get_serialize_handler(content_type).serialize(data)

    def deserialize(self, datastring, content_type):
        """Deserialize a string to a dictionary.

        The string must be in the format of a supported MIME type.
        """
        return self.get_deserialize_handler(content_type).deserialize(
            datastring)

    def get_deserialize_handler(self, content_type):
        handlers = {
            'application/json': JSONDeserializer(),
            'application/xml': XMLDeserializer(self.metadata),
        }

        try:
            return handlers[content_type]
        except Exception:
            raise exception.InvalidContentType(content_type=content_type)
