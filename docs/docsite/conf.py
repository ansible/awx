import sys
import os
import shlex
import warnings

from datetime import datetime
from importlib import import_module

sys.path.insert(0, os.path.abspath('./rst/rest_api/_swagger'))

project = u'Ansible AWX'
copyright = u'2026, Red Hat'
author = u'Red Hat'

pubdateshort = '2026-01-07'
pubdate = datetime.strptime(pubdateshort, '%Y-%m-%d').strftime('%B %d, %Y')

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
# html_title = None
html_title = 'Ansible AWX community documentation'

# A shorter title for the navigation bar.  Default is the same as html_title.
# html_short_title = None
html_short_title = 'AWX community documentation'

htmlhelp_basename = 'AWX_docs'

# include the swagger extension to build rest api reference
#'swagger',
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.ifconfig',
    'sphinx_ansible_theme',
    'sphinxcontrib.redoc',
    'notfound.extension',
    'swagger',
]

notfound_urls_prefix = "/projects/awx/en/latest/"
notfound_template = "404.rst"

html_theme = 'sphinx_ansible_theme'
html_theme_path = ["_static"]

pygments_style = "ansible"
highlight_language = "YAML+Jinja"

source_suffix = '.rst'
master_doc = 'index'

version = 'latest'
shortversion = 'latest'
# The full version, including alpha/beta/rc tags.
release = 'AWX latest'

language = 'en'

locale_dirs = ['locale/']  # path is example but recommended.
gettext_compact = False  # optional.

redoc = [
    {
        'name': 'AWX OpenAPI Reference',
        'page': 'open_api/explorer',
        'spec': 'rst/open_api/schema.json',
        'embed': True,
        'opts': {
            'suppress-warnings': True,
            'hide-hostname': True,
        }
    }
]

# Suppress pkg_resources deprecation from sphinxcontrib-redoc
warnings.filterwarnings(
    'ignore',
    message='pkg_resources is deprecated',
    category=UserWarning,
    module='sphinxcontrib.redoc',
)

rst_epilog = """
.. |atapi| replace:: *AWX API Guide*
.. |atrn| replace:: *AWX Release Notes*
.. |aa| replace:: Ansible Automation
.. |aap| replace:: Ansible Automation Platform
.. |ab| replace:: ansible-builder
.. |at| replace:: AWX
.. |At| replace:: AWX
.. |ah| replace:: Automation Hub
.. |EE| replace:: Execution Environment
.. |EEs| replace:: Execution Environments
.. |Ee| replace:: Execution environment
.. |Ees| replace:: Execution environments
.. |ee| replace:: execution environment
.. |ees| replace:: execution environments
.. |versionshortest| replace:: v%s
.. |pubdateshort| replace:: %s
.. |pubdate| replace:: %s
.. |rhel| replace:: Red Hat Enterprise Linux
.. |rhaa| replace:: Red Hat Ansible Automation
.. |rhaap| replace:: Red Hat Ansible Automation Platform
.. |RHAT| replace:: Red Hat Ansible Automation Platform controller

""" % (
    version,
    pubdateshort,
    pubdate,
)

