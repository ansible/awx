import os
import yaml
import logging

logger = logging.getLogger(__name__)
config_path = os.path.expanduser('~/.psphere/config.yaml')
try:
    config_file = open(config_path, "r")
    PSPHERE_CONFIG = yaml.load(config_file)
    config_file.close()
except IOError:
    logger.warning("Configuration file %s could not be opened, perhaps you"
                   " haven't created one?" % config_path)
    PSPHERE_CONFIG = {"general": {}, "logging": {}}
    pass


def _config_value(section, name, default=None):
    file_value = None
    if name in PSPHERE_CONFIG[section]:
        file_value = PSPHERE_CONFIG[section][name]

    if file_value:
        return file_value
    else:
        return default
