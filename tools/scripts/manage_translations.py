#!/usr/bin/env python
#
# NOTE: This script is based on django's manage_translations.py script
#       (https://github.com/django/django/blob/master/scripts/manage_translations.py)
#
# This python file contains utility scripts to manage Ansible-Tower translations.
# It has to be run inside the ansible-tower git root directory.
#
# The following commands are available:
#
# * update: check for new strings in ansible-tower catalogs, and
#           output how much strings are new/changed.
#
# * stats: output translation statistics at Zanata
#
# * push: update resources in Zanata with the local files
#
# * pull: pull/fetch translations from Zanata
#
# Each command support the --lang option to limit their operation to
# the specified language(s). Use --both option to include UI also.
# For examples,
#
# to update django.pot file, run:
#  $ python tools/scripts/manage_translations.py update
#
# to update both pot files locally, run:
#  $ python tools/scripts/manage_translations.py update --both
#
# to push both pot files (update also) and ja translations, run:
#  $ python tools/scripts/manage_translations.py push --both --lang ja
#
# to pull both translations for Japanese and French, run:
#  $ python tools/scripts/manage_translations.py pull --both --lang ja,fr
#
# to see translations stats at Zanata for Japanese, run:
#  $ python tools/scripts/manage_translations.py pull --both --lang ja

# python
import os
from argparse import ArgumentParser
from subprocess import PIPE, Popen
from xml.etree import ElementTree as ET
from xml.etree.ElementTree import ParseError

# django
import django
from django.conf import settings
from django.core.management import call_command

ZNTA_CONFIG_FRONTEND_TRANS = "tools/scripts/zanata_config/frontend-translations.xml"
ZNTA_CONFIG_BACKEND_TRANS = "tools/scripts/zanata_config/backend-translations.xml"
MIN_TRANS_PERCENT_SETTING = False
MIN_TRANS_PERCENT = '10'


def _print_zanata_project_url(project_config):
    """
    Browser-able Zanata project URL
    """
    project_url = ''
    try:
        zanata_config = ET.parse(project_config).getroot()
        server_url = zanata_config.getchildren()[0].text
        project_id = zanata_config.getchildren()[1].text
        version_id = zanata_config.getchildren()[2].text
        middle_url = "iteration/view/" if server_url[-1:] == '/' else "/iteration/view/"
        project_url = server_url + middle_url + project_id + "/" + version_id + "/documents"
    except (ParseError, IndexError):
        print("Please re-check zanata project configuration.")
    print("Zanata URL: %s\n" % project_url)


def _handle_response(output, errors):
    """
    Prints response received from Zanata client
    """
    if not errors and '\n' in output:
        for response in output.split('\n'):
            print(response)
        return True
    else:
        print(errors.strip())
        return False


def _check_diff(base_path):
    """
    Output the approximate number of changed/added strings in the POT
    """
    po_path = '%s/django.pot' % base_path
    p = Popen("git diff -U0 %s | egrep '^[-+]msgid' | wc -l" % po_path,
              stdout=PIPE, stderr=PIPE, shell=True)
    output, errors = p.communicate()
    num_changes = int(output.strip())
    print("[ %d ] changed/added messages in catalog." % num_changes)


def pull(lang=None, both=None):
    """
    Pull translations .po from Zanata
    """

    command = "zanata pull --project-config %(config)s --lang %(lang)s --disable-ssl-cert"
    lang = lang[0] if lang and len(lang) > 0 else 'en-us'

    if MIN_TRANS_PERCENT_SETTING:
        command += " --min-doc-percent " + MIN_TRANS_PERCENT
    if lang and len(lang) > 0:
        command += " --lang %s" % lang[0]

    if both:
        p = Popen(command % {'config': ZNTA_CONFIG_FRONTEND_TRANS, 'lang': lang},
                  stdout=PIPE, stderr=PIPE, shell=True)
        output, errors = p.communicate()
        _handle_response(output, errors)

    p = Popen(command % {'config': ZNTA_CONFIG_BACKEND_TRANS, 'lang': lang},
              stdout=PIPE, stderr=PIPE, shell=True)
    output, errors = p.communicate()
    _handle_response(output, errors)


def push(lang=None, both=None):
    """
    Push .pot to Zanata
    At Zanata:
        (1) for angularjs - project_type should be gettext - {locale}.po format
        (2) for django - project_type should be podir - {locale}/{filename}.po format
        (3) only required languages should be kept enabled
    This will update/overwrite PO file with translations found for input lang(s)
    [!] POT and PO must remain in sync as messages would overwrite as per POT file
    """
    command = "zanata push --project-config %(config)s --push-type both --force --lang %(lang)s --disable-ssl-cert"
    lang = lang[0] if lang and len(lang) > 0 else 'en-us'

    if both:
        p = Popen(command % {'config': ZNTA_CONFIG_FRONTEND_TRANS, 'lang': lang},
                  stdout=PIPE, stderr=PIPE, shell=True)
        output, errors = p.communicate()
        if _handle_response(output, errors):
            _print_zanata_project_url(ZNTA_CONFIG_FRONTEND_TRANS)

    p = Popen(command % {'config': ZNTA_CONFIG_BACKEND_TRANS, 'lang': lang},
              stdout=PIPE, stderr=PIPE, shell=True)
    output, errors = p.communicate()
    if _handle_response(output, errors):
        _print_zanata_project_url(ZNTA_CONFIG_BACKEND_TRANS)


def stats(lang=None, both=None):
    """
    Get translation stats from Zanata
    """
    command = "zanata stats --project-config %(config)s --lang %(lang)s --disable-ssl-cert --word"
    lang = lang[0] if lang and len(lang) > 0 else 'en-us'

    if both:
        p = Popen(command % {'config': ZNTA_CONFIG_FRONTEND_TRANS, 'lang': lang},
                  stdout=PIPE, stderr=PIPE, shell=True)
        output, errors = p.communicate()
        _handle_response(output, errors)

    p = Popen(command % {'config': ZNTA_CONFIG_BACKEND_TRANS, 'lang': lang},
              stdout=PIPE, stderr=PIPE, shell=True)
    output, errors = p.communicate()
    _handle_response(output, errors)


def update(lang=None, both=None):
    """
    Update (1) awx/locale/django.pot and/or
     (2) awx/ui/po/ansible-tower-ui.pot files with
    new/updated translatable strings.
    """
    settings.configure()
    django.setup()
    print("Updating catalog for Ansible Tower:")

    if both:
        print("Angular...")
        p = Popen("make pot", stdout=PIPE, stderr=PIPE, shell=True)
        output, errors = p.communicate()
        _handle_response(output, errors)

    print("Django...")
    lang = (lang[0].split(',') if ',' in lang[0] else lang) if lang else []
    os.chdir(os.path.join(os.getcwd(), 'awx'))
    call_command('makemessages', '--keep-pot', locale=lang or ['en-us'])
    # Output changed stats
    _check_diff(os.path.join(os.getcwd(), 'locale'))


if __name__ == "__main__":

    try:
        devnull = open(os.devnull)
        Popen(["zanata"], stdout=devnull, stderr=devnull).communicate()
    except OSError as e:
        if e.errno == os.errno.ENOENT:
            print('''
            You need zanata python client, install it.
             1. Install zanta python client
             2. Create ~/.config/zanata.ini file:
                   $ vim ~/.config/zanata.ini
                    [servers]
                    translate_zanata_org.url=https://translate.engineering.redhat.com/
                    translate_zanata_org.username=ansibletoweruser
                    translate_zanata_org.key=
                ''')

            exit(1)

    RUNABLE_SCRIPTS = ('update', 'stats', 'pull', 'push')

    parser = ArgumentParser()
    parser.add_argument('cmd', nargs=1, choices=RUNABLE_SCRIPTS)
    parser.add_argument("-l", "--lang", action='append', help="specify comma seperated locales")
    parser.add_argument("-u", "--both", action='store_true', help="specify to include ui tasks")
    options = parser.parse_args()

    eval(options.cmd[0])(options.lang, options.both)
