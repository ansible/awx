import glob
import os
import yaml
import logging

from psphere import config
from psphere.errors import TemplateNotFoundError

logger = logging.getLogger(__name__)

template_path = os.path.expanduser(config._config_value("general",
                                                        "template_dir"))

def _merge(first, second):
    """Merge a list of templates.
    
    The templates will be merged with values in higher templates
    taking precedence.

    :param templates: The templates to merge.
    :type templates: list

    """
    return dict(first.items() + second.items())


def load_template(name=None):
    """Loads a template of the specified name.

    Templates are placed in the <template_dir> directory in YAML format with
    a .yaml extension.

    If no name is specified then the function will return the default
    template (<template_dir>/default.yaml) if it exists.
    
    :param name: The name of the template to load.
    :type name: str or None (default)

    """
    if name is None:
        name = "default"

    logger.info("Loading template with name %s", name)
    try:
        template_file = open("%s/%s.yaml" % (template_path, name))
    except IOError:
        raise TemplateNotFoundError

    template = yaml.safe_load(template_file)
    template_file.close()
    if "extends" in template:
        logger.debug("Merging %s with %s", name, template["extends"])
        template = _merge(load_template(template["extends"]), template)

    return template


def list_templates():
    """Returns a list of all templates."""
    templates = [f for f in glob.glob(os.path.join(template_path, '*.yaml'))]
    return templates
