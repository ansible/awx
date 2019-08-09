import yaml

from awxkit.utils import PseudoNamespace


class HasVariables(object):

    @property
    def variables(self):
        return PseudoNamespace(yaml.load(self.json.variables, Loader=yaml.FullLoader))
