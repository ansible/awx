import sys
import os
import shlex

from datetime import datetime
from importlib import import_module

sys.path.insert(0, os.path.abspath('./rst/rest_api/_swagger'))

project = u'Ansible AWX'
copyright = u'2023, Red Hat'
author = u'Red Hat'

pubdateshort = '2023-08-04'
pubdate = datetime.strptime(pubdateshort, '%Y-%m-%d').strftime('%B %d, %Y')

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
#html_title = None
html_title = 'Ansible AWX community documentation'

# A shorter title for the navigation bar.  Default is the same as html_title.
#html_short_title = None
html_short_title = 'AWX community documentation'

htmlhelp_basename = 'AWX_docs'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.ifconfig',
    'sphinx_ansible_theme',
    'swagger',
]

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

# The following content is not available as part of an RST document but as
# part of an html layout. This is why we are integrating the translation here.
ansible_latest_link = {
    'ko': 'Automation Controller의 최신 버전을 사용하고 계십니까? 사용 중인 컨트롤러 버전과 가장 일치하는 <a class="DocSiteProduct-versionheader" href="http://docs.ansible.com/automation.html">Automation Controller 문서</a> 세트를 찾으십시오.',
    'ja': '最新の Automation Controller を利用されていますか?お使いの Controller に最適な <a class="DocSiteProduct-versionheader" href="http://docs.ansible.com/automation.html">Automation Controller</a> ドキュメントをご参照ください。',
    'zh': '您是否正在使用最新和最好的 Automation Controller 版本? 请选择与您的 Controller 版本匹配的 <a class="DocSiteProduct-versionheader" href="http://docs.ansible.com/automation.html">Automation Controller 文档</a>.',
    'en': 'Are you using the latest and greatest version of Automation Controller? Find the <a class="DocSiteProduct-versionheader" href="http://docs.ansible.com/automation.html">Automation Controller documentation</a> set which best matches your version of the controller.'
}

lang = os.getenv('LANGUAGE', 'en')
if lang not in ansible_latest_link:
    lang = 'en'
latest_link = ansible_latest_link[lang]

locale_dirs = ['locale/']   # path is example but recommended.
gettext_compact = False     # optional.

rst_epilog = """
.. |atqi| replace:: *AWX Quick Installation Guide*
.. |atqs| replace:: *AWX Quick Setup Guide*
.. |atir| replace:: *AWX Installation and Reference Guide*
.. |ata| replace:: *AWX Administration Guide*
.. |atu| replace:: *AWX User Guide*
.. |atumg| replace:: *AWX Upgrade and Migration Guide*
.. |atapi| replace:: *AWX API Guide*
.. |atrn| replace:: *AWX Release Notes*
.. |aa| replace:: Ansible Automation
.. |AA| replace:: Automation Analytics
.. |aap| replace:: Ansible Automation Platform
.. |ab| replace:: ansible-builder
.. |ap| replace:: Automation Platform
.. |at| replace:: automation controller
.. |At| replace:: Automation controller
.. |ah| replace:: Automation Hub
.. |EE| replace:: Execution Environment
.. |EEs| replace:: Execution Environments
.. |Ee| replace:: Execution environment
.. |Ees| replace:: Execution environments
.. |ee| replace:: execution environment
.. |ees| replace:: execution environments
.. |atversion| replace:: Automation Controller Version %s
.. |atversionshort| replace:: Automation Controller v%s
.. |atversionshortest| replace:: Automation Controller %s
.. |versionshortest| replace:: v%s
.. [pubdateshort| replace:: %s
.. |pubdate| replace:: %s
.. |rhel| replace:: Red Hat Enterprise Linux
.. |rhaa| replace:: Red Hat Ansible Automation
.. |rhaap| replace:: Red Hat Ansible Automation Platform
.. |RHAT| replace:: Red Hat Ansible Automation Platform controller
.. |atng| replace:: Automation Controller Networking Guide
.. |atn| replace:: Controller Networking

""" % (version, version, shortversion, version, pubdateshort, pubdate)
