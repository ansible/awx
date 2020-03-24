# Python
import urllib.parse
from collections import deque
# Django
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType


NAMED_URL_RES_DILIMITER = "++"
NAMED_URL_RES_INNER_DILIMITER = "+"
NAMED_URL_RES_DILIMITER_ENCODE = "%2B"
URL_PATH_RESERVED_CHARSET = {}
for c in ';/?:@=&[]':
    URL_PATH_RESERVED_CHARSET[c] = urllib.parse.quote(c, safe='')
FK_NAME = 0
NEXT_NODE = 1

NAME_EXCEPTIONS = {
    "custom_inventory_scripts": "inventory_scripts"
}


class GraphNode(object):

    def __init__(self, model, fields, adj_list):
        self.model = model
        self.found = False
        self.obj = None
        self.fields = fields
        self.adj_list = adj_list
        self.counter = 0

    def _handle_unexpected_model_url_names(self, model_url_name):
        if model_url_name in NAME_EXCEPTIONS:
            return NAME_EXCEPTIONS[model_url_name]
        return model_url_name

    @property
    def model_url_name(self):
        if not hasattr(self, '_model_url_name'):
            self._model_url_name = self.model._meta.verbose_name_plural.replace(' ', '_')
            self._model_url_name = self._handle_unexpected_model_url_names(self._model_url_name)
        return self._model_url_name

    @property
    def named_url_format(self):
        named_url_components = []
        stack = [self]
        current_fk_name = ''
        while stack:
            if stack[-1].counter == 0:
                named_url_component = NAMED_URL_RES_INNER_DILIMITER.join(
                    ["<%s>" % (current_fk_name + field)
                     for field in stack[-1].fields]
                )
                named_url_components.append(named_url_component)
            if stack[-1].counter >= len(stack[-1].adj_list):
                stack[-1].counter = 0
                stack.pop()
            else:
                to_append = stack[-1].adj_list[stack[-1].counter][NEXT_NODE]
                current_fk_name = "%s." % (stack[-1].adj_list[stack[-1].counter][FK_NAME],)
                stack[-1].counter += 1
                stack.append(to_append)
        return NAMED_URL_RES_DILIMITER.join(named_url_components)

    @property
    def named_url_repr(self):
        ret = {}
        ret['fields'] = self.fields
        ret['adj_list'] = [[x[FK_NAME], x[NEXT_NODE].model_url_name] for x in self.adj_list]
        return ret

    def _encode_uri(self, text):
        '''
        Performance assured: http://stackoverflow.com/a/27086669
        '''
        for c in URL_PATH_RESERVED_CHARSET:
            if not isinstance(text, str):
                text = str(text)  # needed for WFJT node creation, identifier temporarily UUID4 type
            if c in text:
                text = text.replace(c, URL_PATH_RESERVED_CHARSET[c])
        text = text.replace(NAMED_URL_RES_INNER_DILIMITER,
                            '[%s]' % NAMED_URL_RES_INNER_DILIMITER)
        return text

    def generate_named_url(self, obj):
        self.obj = obj
        named_url = []
        stack = [self]
        while stack:
            if stack[-1].counter == 0:
                named_url_item = [self._encode_uri(getattr(stack[-1].obj, field, ''))
                                  for field in stack[-1].fields]
                named_url.append(NAMED_URL_RES_INNER_DILIMITER.join(named_url_item))
            if stack[-1].counter >= len(stack[-1].adj_list):
                stack[-1].counter = 0
                stack[-1].obj = None
                stack.pop()
            else:
                next_ = stack[-1].adj_list[stack[-1].counter]
                stack[-1].counter += 1
                next_obj = getattr(stack[-1].obj, next_[FK_NAME], None)
                if next_obj is not None:
                    next_[NEXT_NODE].obj = next_obj
                    stack.append(next_[NEXT_NODE])
                else:
                    named_url.append('')
        return NAMED_URL_RES_DILIMITER.join(named_url)


    def _process_top_node(self, named_url_names, kwargs, prefixes, stack, idx):
        if stack[-1].counter == 0:
            if idx >= len(named_url_names):
                return idx, False
            if not named_url_names[idx]:
                stack[-1].counter = 0
                stack.pop()
                if prefixes:
                    prefixes.pop()
                idx += 1
                return idx, True
            named_url_parts = named_url_names[idx].split(NAMED_URL_RES_INNER_DILIMITER)
            if len(named_url_parts) != len(stack[-1].fields):
                return idx, False
            evolving_prefix = '__'.join(prefixes)
            for attr_name, attr_value in zip(stack[-1].fields, named_url_parts):
                attr_name = ("__%s" % attr_name) if evolving_prefix else attr_name
                if isinstance(attr_value, str):
                    attr_value = urllib.parse.unquote(attr_value)
                kwargs[evolving_prefix + attr_name] = attr_value
            idx += 1
        if stack[-1].counter >= len(stack[-1].adj_list):
            stack[-1].counter = 0
            stack.pop()
            if prefixes:
                prefixes.pop()
        else:
            to_append = stack[-1].adj_list[stack[-1].counter]
            stack[-1].counter += 1
            prefixes.append(to_append[FK_NAME])
            stack.append(to_append[NEXT_NODE])
        return idx, True

    def populate_named_url_query_kwargs(self, kwargs, named_url, ignore_digits=True):
        if ignore_digits and named_url.isdigit() and int(named_url) > 0:
            return False
        named_url = named_url.replace('[%s]' % NAMED_URL_RES_INNER_DILIMITER,
                                      NAMED_URL_RES_DILIMITER_ENCODE)
        named_url_names = named_url.split(NAMED_URL_RES_DILIMITER)
        prefixes = []
        stack = [self]
        idx = 0
        while stack:
            idx, is_valid = self._process_top_node(
                named_url_names, kwargs, prefixes, stack, idx
            )
            if not is_valid:
                return False
        return idx == len(named_url_names)

    def add_bindings(self):
        if self.model_url_name not in settings.NAMED_URL_FORMATS:
            settings.NAMED_URL_FORMATS[self.model_url_name] = self.named_url_format
            settings.NAMED_URL_GRAPH_NODES[self.model_url_name] = self.named_url_repr
            settings.NAMED_URL_MAPPINGS[self.model_url_name] = self.model

    def remove_bindings(self):
        if self.model_url_name in settings.NAMED_URL_FORMATS:
            settings.NAMED_URL_FORMATS.pop(self.model_url_name)
            settings.NAMED_URL_GRAPH_NODES.pop(self.model_url_name)
            settings.NAMED_URL_MAPPINGS.pop(self.model_url_name)


def _get_all_unique_togethers(model):
    queue = deque()
    queue.append(model)
    ret = []
    try:
        if model._meta.get_field('name').unique:
            ret.append(('name',))
    except Exception:
        pass
    while len(queue) > 0:
        model_to_backtrack = queue.popleft()
        uts = model_to_backtrack._meta.unique_together
        if len(uts) > 0 and not isinstance(uts[0], tuple):
            ret.append(uts)
        else:
            ret.extend(uts)
        soft_uts = getattr(model_to_backtrack, 'SOFT_UNIQUE_TOGETHER', [])
        ret.extend(soft_uts)
        for parent_class in model_to_backtrack.__bases__:
            if issubclass(parent_class, models.Model) and\
                    hasattr(parent_class, '_meta') and\
                    hasattr(parent_class._meta, 'unique_together') and\
                    isinstance(parent_class._meta.unique_together, tuple):
                queue.append(parent_class)
    ret.sort(key=lambda x: len(x))
    return tuple(ret)


def _check_unique_together_fields(model, ut):
    name_field = None
    fk_names = []
    fields = []
    is_valid = True
    for field_name in ut:
        field = model._meta.get_field(field_name)
        if field_name in ('name', 'identifier'):
            name_field = field_name
        elif type(field) == models.ForeignKey and field.related_model != model:
            fk_names.append(field_name)
        elif issubclass(type(field), models.CharField) and field.choices:
            fields.append(field_name)
        else:
            is_valid = False
            break
    if not is_valid:
        return (), (), is_valid
    fk_names.sort()
    fields.sort(reverse=True)
    if name_field:
        fields.append(name_field)
    fields.reverse()
    return tuple(fk_names), tuple(fields), is_valid


def _generate_configurations(nodes):
    if not nodes:
        return
    idx = 0
    stack = [nodes[0][1]]
    idx_stack = [0]
    configuration = {}
    while stack:
        if idx_stack[-1] >= len(stack[-1]):
            stack.pop()
            idx_stack.pop()
            configuration.pop(nodes[idx][0])
            idx -= 1
        else:
            if len(configuration) == len(stack):
                configuration.pop(nodes[idx][0])
            configuration[nodes[idx][0]] = tuple(stack[-1][idx_stack[-1]])
            idx_stack[-1] += 1
            if idx == len(nodes) - 1:
                yield configuration.copy()
            else:
                idx += 1
                stack.append(nodes[idx][1])
                idx_stack.append(0)


def _dfs(configuration, model, graph, dead_ends, new_deadends, parents):
    parents.add(model)
    fields, fk_names = configuration[model][0][:], configuration[model][1][:]
    adj_list = []
    for fk_name in fk_names:
        next_model = model._meta.get_field(fk_name).related_model
        if issubclass(next_model, ContentType):
            continue
        if next_model not in configuration or\
                next_model in dead_ends or\
                next_model in new_deadends or\
                next_model in parents:
            new_deadends.add(model)
            parents.remove(model)
            return False
        if next_model not in graph and\
                not _dfs(
                    configuration, next_model, graph,
                    dead_ends, new_deadends, parents
                ):
            new_deadends.add(model)
            parents.remove(model)
            return False
        adj_list.append((fk_name, graph[next_model]))
    graph[model] = GraphNode(model, fields, adj_list)
    parents.remove(model)
    return True


def _generate_single_graph(configuration, dead_ends):
    new_deadends = set()
    graph = {}
    for model in configuration:
        if model not in graph and model not in new_deadends:
            _dfs(configuration, model, graph, dead_ends, new_deadends, set())
    return graph


def generate_graph(models):
    settings.NAMED_URL_FORMATS = {}
    settings.NAMED_URL_GRAPH_NODES = {}
    settings.NAMED_URL_MAPPINGS = {}
    candidate_nodes = {}
    dead_ends = set()
    for model in models:
        uts = _get_all_unique_togethers(model)
        for ut in uts:
            fk_names, fields, is_valid = _check_unique_together_fields(model, ut)
            if is_valid:
                candidate_nodes.setdefault(model, [])
                candidate_nodes[model].append([fields, fk_names])
        if model not in candidate_nodes:
            dead_ends.add(model)
    candidate_nodes = list(candidate_nodes.items())
    largest_graph = {}
    for configuration in _generate_configurations(candidate_nodes):
        candidate_graph = _generate_single_graph(configuration, dead_ends)
        if len(largest_graph) < len(candidate_graph):
            largest_graph = candidate_graph
        if len(largest_graph) == len(candidate_nodes):
            break
    settings.NAMED_URL_GRAPH = largest_graph
    for node in settings.NAMED_URL_GRAPH.values():
        node.add_bindings()


def reset_counters():
    for node in settings.NAMED_URL_GRAPH.values():
        node.counter = 0
