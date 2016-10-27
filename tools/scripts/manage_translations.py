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
# * stats: output statistics for each language
#
# * pull: pull/fetch translations from Zanata
#
# * push: update resources in Zanata with the local files
#
# Each command support the --lang option to limit their operation to
# the specified language(s). For example,
# to pull translations for Japanese and French, run:
#
#  $ python tools/scripts/manage_translations.py pull --lang ja,fr

import os
from argparse import ArgumentParser
from subprocess import PIPE, Popen, call

import django
from django.conf import settings
from django.core.management import call_command


PROJECT_CONFIG = "config/zanata.xml"
MIN_TRANS_PERCENT_SETTING = False
MIN_TRANS_PERCENT = '10'


def _handle_response(output, errors):
    if not errors and '\n' in output:
        for response in output.split('\n'):
            print(response)
    else:
        print(errors.strip())


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

    command = "zanata pull --project-config %(config)s --disable-ssl-cert"

    if MIN_TRANS_PERCENT_SETTING:
        command += " --min-doc-percent " + MIN_TRANS_PERCENT
    if lang:
        command += " --lang %s" % lang[0]

    p = Popen(command % {'config': PROJECT_CONFIG},
              stdout=PIPE, stderr=PIPE, shell=True)
    output, errors = p.communicate()
    _handle_response(output, errors)


def push(lang=None, both=None):
    """
    Push django.pot to Zanata
    At Zanata:
        (1) project_type should be podir - {locale}/{filename}.po format
        (2) only required languages should be kept enabled
    """
    p = Popen("zanata push --project-config %(config)s --disable-ssl-cert" %
              {'config': PROJECT_CONFIG}, stdout=PIPE, stderr=PIPE, shell=True)
    output, errors = p.communicate()
    _handle_response(output, errors)


def stats(lang=None, both=None):
    """
    Get translation stats from Zanata
    """
    command = "zanata stats --project-config %(config)s --disable-ssl-cert"
    if lang:
        command += " --lang %s" % lang[0]

    p = Popen(command % {'config': PROJECT_CONFIG},
              stdout=PIPE, stderr=PIPE, shell=True)
    output, errors = p.communicate()
    _handle_response(output, errors)


def update(lang=None, both=None):
    """
    Update the awx/locale/django.pot files with
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
    call_command('makemessages', '--keep-pot', locale=lang)
    # Output changed stats
    _check_diff(os.path.join(os.getcwd(), 'locale'))


if __name__ == "__main__":

    try:
        devnull = open(os.devnull)
        Popen(["zanata"], stdout=devnull, stderr=devnull).communicate()
    except OSError as e:
        if e.errno == os.errno.ENOENT:
            print('''
            You need zanata-python-client, install it.
             1. Install zanata-python-client, use
                   $ dnf install zanata-python-client
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
