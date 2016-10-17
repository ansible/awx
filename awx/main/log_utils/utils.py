import os
import yaml


def parse_config_file():
    """
    Find the .splunk_logger config file in the current directory, or in the
    user's home and parse it. The one in the current directory has precedence.
    
    :return: A tuple with:
                - project_id
                - access_token
    """
    for filename in ('.splunk_logger', os.path.expanduser('~/.splunk_logger')):

        project_id, access_token, api_domain = _parse_config_file_impl(filename)

        if project_id is not None\
        and access_token is not None\
        and api_domain is not None:
            return project_id, access_token, api_domain

    else:
        return None, None, None


def _parse_config_file_impl(filename):
    """
    Format for the file is:
    
         credentials:
             project_id: ...
             access_token: ...
             api_domain: ...
    
    :param filename: The filename to parse
    :return: A tuple with:
                - project_id
                - access_token
                - api_domain
    """
    try:
        doc = yaml.load(file(filename).read())
        
        project_id = doc["credentials"]["project_id"]
        access_token = doc["credentials"]["access_token"]
        api_domain = doc["credentials"]["api_domain"]
        
        return project_id, access_token, api_domain
    except:
        return None, None, None


def get_config_from_env():
    return (os.environ.get('SPLUNK_PROJECT_ID', None),
            os.environ.get('SPLUNK_ACCESS_TOKEN', None),
            os.environ.get('SPLUNK_API_DOMAIN', None))