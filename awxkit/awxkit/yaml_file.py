import os
import yaml
import glob
import logging

from awxkit.exceptions import PathTraversalError

log = logging.getLogger(__name__)


file_pattern_cache = {}
file_path_cache = {}


class Loader(yaml.SafeLoader):
    def __init__(self, stream):
        raw_root = os.path.split(stream.name)[0]
        # Keep '' for stdin so extractFile() rejects !include with no base dir
        self._root = os.path.realpath(raw_root) if raw_root else ''
        super(Loader, self).__init__(stream)
        Loader.add_constructor('!include', Loader.include)
        Loader.add_constructor('!import', Loader.include)

    def include(self, node):
        if isinstance(node, yaml.ScalarNode):
            return self.extractFile(self.construct_scalar(node))

        elif isinstance(node, yaml.SequenceNode):
            result = []
            for filename in self.construct_sequence(node):
                result += self.extractFile(filename)
            return result

        elif isinstance(node, yaml.MappingNode):
            result = {}
            for k, v in self.construct_mapping(node).items():
                result[k] = self.extractFile(v)[k]
            return result

        else:
            log.error("unrecognised node type in !include statement")
            raise yaml.constructor.ConstructorError

    def _validate_path(self, filename, resolved_path):
        real_path = os.path.realpath(resolved_path)
        root_prefix = self._root + os.sep
        if not (real_path.startswith(root_prefix) or real_path == self._root):
            raise PathTraversalError("YAML !include path '{}' is not allowed".format(filename))

    def extractFile(self, filename):
        if not self._root:
            raise PathTraversalError("YAML !include directive is not supported when reading from stdin")

        if os.path.isabs(filename):
            raise PathTraversalError("YAML !include path '{}' is not allowed".format(filename))

        file_pattern = os.path.join(self._root, filename)

        normalized = os.path.normpath(file_pattern)
        root_prefix = self._root + os.sep
        if not (normalized.startswith(root_prefix) or normalized == self._root):
            raise PathTraversalError("YAML !include path '{}' is not allowed".format(filename))
        log.debug('Will attempt to extract schema from: {0}'.format(file_pattern))
        if file_pattern in file_pattern_cache:
            log.debug('File pattern cache hit: {0}'.format(file_pattern))
            return file_pattern_cache[file_pattern]

        data = dict()
        for file_path in glob.glob(file_pattern):
            file_path = os.path.abspath(file_path)
            self._validate_path(filename, file_path)
            if file_path in file_path_cache:
                log.debug('Schema cache hit: {0}'.format(file_path))
                path_data = file_path_cache[file_path]
            else:
                log.debug('Loading schema from {0}'.format(file_path))
                with open(file_path, 'r') as f:
                    path_data = yaml.load(f, Loader)
                file_path_cache[file_path] = path_data
            data.update(path_data)

        file_pattern_cache[file_pattern] = data
        return data


def load_file(filename):
    """Loads a YAML file from the given filename.

    If the filename is omitted or None, attempts will be made to load it from
    its normal location in the parent of the utils directory.

    The awx_data dict loaded with this method supports value randomization,
    thanks to the RandomizeValues class. See that class for possible options

    Example usage in data.yaml (quotes are important!):

    top_level:
      list:
      - "{random_str}"
      - "{random_int}"
      - "{random_uuid}"
      random_thing: "{random_string:24}"
    """
    from py.path import local

    if filename is None:
        this_file = os.path.abspath(__file__)
        path = local(this_file).new(basename='../data.yaml')
    else:
        path = local(filename)

    if path.check():
        with open(path, 'r') as fp:
            # FIXME - support load_all()
            return yaml.load(fp, Loader=Loader)
    else:
        msg = 'Unable to load data file at %s' % path
        raise Exception(msg)
