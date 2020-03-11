import textwrap
import pytest

# AWX
from awx.main.redact import UriCleaner
from awx.main.tests.URI import URI

TEST_URIS = [
    URI('no host', scheme='https', username='myusername', password='mypass', host=None),
    URI('no host', scheme='https', username='myusername', password='mypass*********', host=None),
    URI('http', scheme='http'),
    URI('https', scheme='https'),
    URI('no password', password=''),
    URI('no host', host=''),
    URI('host with port', host='host.com:22'),
    URI('host with @', host='host.com:22'),
    URI('host with @, password with @ at the end', password='mypasswordwith@', host='@host.com'),
    URI('no host, with space', host=' '),
    URI('password is a space', password='%20%20'),
    URI('no password field', password=None),
    URI('no username no password', username=None, password=None),
    URI('password with @ at the end', password='mypasswordwitha@'),
    URI('password with @@ at the end', password='mypasswordwitha@@'),
    URI('password with @@@ at the end', password='mypasswordwitha@@@'),
    URI('password with @@@@ at the end', password='mypasswordwitha@@@@'),
    URI('password with @a@@ at the end', password='mypasswordwitha@a@@'),
    URI('password with @@@a at the end', password='mypasswordwitha@@@a'),
    URI('password with a @ in the middle', password='pa@ssword'),
    URI('url with @', password='pa@ssword', host='googly.com/whatever@#$:stuff@.com/'),
]

TEST_CLEARTEXT = []
# Arguably, this is a regression test given the below data.
# regression data https://trello.com/c/cdUELgVY/
uri = URI(scheme="https", username="myusername", password="mypasswordwith%40", host="nonexistant.ansible.com/ansible.git/")
TEST_CLEARTEXT.append({
    'uri' : uri,
    'text' : textwrap.dedent("""\
        PLAY [all] ********************************************************************

        TASK: [delete project directory before update] ********************************
        skipping: [localhost]

        TASK: [update project using git and accept hostkey] ***************************
        skipping: [localhost]

        TASK: [update project using git] **********************************************
        failed: [localhost] => {"cmd": "/usr/bin/git ls-remote https://%s:%s -h refs/heads/HEAD", "failed": true, "rc": 128}
        stderr: fatal: unable to access '%s': Could not resolve host: nonexistant.ansible.com

        msg: fatal: unable to access '%s': Could not resolve host: nonexistant.ansible.com

        FATAL: all hosts have already failed -- aborting

        PLAY RECAP ********************************************************************
                   to retry, use: --limit @/root/project_update.retry

        localhost                  : ok=0    changed=0    unreachable=0    failed=1

        """ % (uri.username, uri.password, str(uri), str(uri))),
    'host_occurrences' : 2
})

uri = URI(scheme="https", username="Dhh3U47nmC26xk9PKscV", password="PXPfWW8YzYrgS@E5NbQ2H@", host="github.ginger.com/theirrepo.git/info/refs")
TEST_CLEARTEXT.append({
    'uri' : uri,
    'text' : textwrap.dedent("""\
        TASK: [update project using git] **
                    failed: [localhost] => {"cmd": "/usr/bin/git ls-remote https://REDACTED:********", "failed": true, "rc": 128}
                    stderr: error: Couldn't resolve host '@%s' while accessing %s

                    fatal: HTTP request failed

                    msg: error: Couldn't resolve host '@%s' while accessing %s

                    fatal: HTTP request failed
        """ % (uri.host, str(uri), uri.host, str(uri))),
    'host_occurrences' : 4
})


@pytest.mark.parametrize('username, password, not_uri, expected', [
    ('', '', 'www.famfamfam.com](http://www.famfamfam.com/fijdlfd', 'www.famfamfam.com](http://www.famfamfam.com/fijdlfd'),
    ('', '', 'https://www.famfamfam.com](http://www.famfamfam.com/fijdlfd', '$encrypted$'),
    ('root', 'gigity', 'https://root@gigity@www.famfamfam.com](http://www.famfamfam.com/fijdlfd', '$encrypted$'),
    ('root', 'gigity@', 'https://root:gigity@@@www.famfamfam.com](http://www.famfamfam.com/fijdlfd', '$encrypted$'),
])
# should redact sensitive usernames and passwords
def test_non_uri_redact(username, password, not_uri, expected):
    redacted_str = UriCleaner.remove_sensitive(not_uri)
    if username:
        assert username not in redacted_str
    if password:
        assert password not in redacted_str

    assert redacted_str == expected


def test_multiple_non_uri_redact():
    non_uri = 'https://www.famfamfam.com](http://www.famfamfam.com/fijdlfd hi '
    non_uri += 'https://www.famfamfam.com](http://www.famfamfam.com/fijdlfd world '
    non_uri += 'https://www.famfamfam.com](http://www.famfamfam.com/fijdlfd foo '
    non_uri += 'https://foo:bar@giggity.com bar'
    redacted_str = UriCleaner.remove_sensitive(non_uri)
    assert redacted_str == '$encrypted$ hi $encrypted$ world $encrypted$ foo https://$encrypted$:$encrypted$@giggity.com bar'


# should replace secret data with safe string, UriCleaner.REPLACE_STR
@pytest.mark.parametrize('uri', TEST_URIS)
def test_uri_scm_simple_replaced(uri):
    redacted_str = UriCleaner.remove_sensitive(str(uri))
    assert redacted_str.count(UriCleaner.REPLACE_STR) == uri.get_secret_count()


# should redact multiple uris in text
@pytest.mark.parametrize('uri', TEST_URIS)
def test_uri_scm_multiple(uri):
    cleartext = ''
    cleartext += str(uri) + ' '
    cleartext += str(uri) + '\n'

    redacted_str = UriCleaner.remove_sensitive(str(uri))
    if uri.username:
        assert uri.username not in redacted_str
    if uri.password:
        assert uri.password not in redacted_str


# should replace multiple secret data with safe string
@pytest.mark.parametrize('uri', TEST_URIS)
def test_uri_scm_multiple_replaced(uri):
    cleartext = ''
    find_count = 0

    cleartext += str(uri) + ' '
    find_count += uri.get_secret_count()

    cleartext += str(uri) + '\n'
    find_count += uri.get_secret_count()

    redacted_str = UriCleaner.remove_sensitive(cleartext)
    assert redacted_str.count(UriCleaner.REPLACE_STR) == find_count


# should redact and replace multiple secret data within a complex cleartext blob
@pytest.mark.parametrize('test_data', TEST_CLEARTEXT)
def test_uri_scm_cleartext_redact_and_replace(test_data):
    uri = test_data['uri']
    redacted_str = UriCleaner.remove_sensitive(test_data['text'])
    assert uri.username not in redacted_str
    assert uri.password not in redacted_str
    # Ensure the host didn't get redacted
    assert redacted_str.count(uri.host) == test_data['host_occurrences']


@pytest.mark.timeout(1)
def test_large_string_performance():
    length = 100000
    redacted = UriCleaner.remove_sensitive('x' * length)
    assert len(redacted) == length

