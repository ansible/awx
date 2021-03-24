import yaml

from awxkit.utils import PseudoNamespace


class HasVariables(object):
    @property
    def variables(self):
        return PseudoNamespace(yaml.safe_load(self.json.variables))
