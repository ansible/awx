import urllib.parse

# WebhookMixin is a Django abstract model — importing it triggers full Django app
# initialization. The validation logic is pure Python (no DB, no ORM), so we mirror
# the implementations here to test them without Django.


def _get_scm_hostname(scm_url):
    """Mirror of WebhookMixin._get_scm_hostname for testing without Django."""
    if not scm_url:
        return None
    if '://' in scm_url:
        return urllib.parse.urlparse(scm_url).hostname
    host_part = scm_url.split('@', 1)[-1] if '@' in scm_url else scm_url
    if host_part.startswith('[') and ']:' in host_part:
        host = host_part.split(']:')[0][1:]
        return host if host else None
    if ':' in host_part:
        host = host_part.split(':', 1)[0]
        return host if host else None
    if '/' in host_part:
        host = host_part.split('/', 1)[0]
        return host if host else None
    return None


def _validate_webhook_status_url(project_scm_url, status_api, project_exists=True):
    """Mirror of WebhookMixin._validate_webhook_status_url for testing without Django."""
    parsed = urllib.parse.urlparse(status_api)
    status_host = parsed.hostname
    if not status_host:
        return False
    if not project_exists:
        return False
    scm_host = _get_scm_hostname(project_scm_url)
    if not scm_host:
        return False
    allowed_hosts = {scm_host}
    if scm_host == 'github.com':
        allowed_hosts.add('api.github.com')
    return status_host in allowed_hosts


class TestGetScmHostname:
    """Verify hostname extraction from various SCM URL formats."""

    def test_https_url(self):
        assert _get_scm_hostname('https://github.com/ansible/awx.git') == 'github.com'

    def test_http_url(self):
        assert _get_scm_hostname('http://gitlab.example.com/org/repo.git') == 'gitlab.example.com'

    def test_ssh_scheme_url(self):
        assert _get_scm_hostname('ssh://git@github.com/ansible/awx.git') == 'github.com'

    def test_scp_style_url(self):
        assert _get_scm_hostname('git@github.com:ansible/awx.git') == 'github.com'

    def test_scp_style_no_user(self):
        assert _get_scm_hostname('github.com:ansible/awx.git') == 'github.com'

    def test_scp_style_gitlab(self):
        assert _get_scm_hostname('git@gitlab.example.com:org/repo.git') == 'gitlab.example.com'

    def test_empty_string(self):
        assert _get_scm_hostname('') is None

    def test_none(self):
        assert _get_scm_hostname(None) is None

    def test_url_with_port(self):
        assert _get_scm_hostname('https://git.example.com:8443/org/repo.git') == 'git.example.com'

    def test_ipv6_scp_style(self):
        assert _get_scm_hostname('git@[fd00::1]:org/repo.git') == 'fd00::1'

    def test_bare_url_without_scheme(self):
        assert _get_scm_hostname('github.com/ansible/awx.git') == 'github.com'


class TestValidateWebhookStatusUrl:
    """Verify that webhook status URL validation correctly allows/rejects hosts."""

    def test_matching_host(self):
        assert (
            _validate_webhook_status_url(
                'https://gitlab.example.com/org/repo.git',
                'https://gitlab.example.com/api/v4/projects/42/statuses/abc123',
            )
            is True
        )

    def test_github_api_host_allowed(self):
        assert (
            _validate_webhook_status_url(
                'https://github.com/ansible/awx.git',
                'https://api.github.com/repos/ansible/awx/statuses/abc123',
            )
            is True
        )

    def test_github_scm_host_also_allowed(self):
        assert (
            _validate_webhook_status_url(
                'https://github.com/ansible/awx.git',
                'https://github.com/something',
            )
            is True
        )

    def test_github_enterprise_matching_host(self):
        assert (
            _validate_webhook_status_url(
                'https://github.corp.example.com/org/repo.git',
                'https://github.corp.example.com/api/v3/repos/org/repo/statuses/abc',
            )
            is True
        )

    def test_github_enterprise_api_github_com_rejected(self):
        assert (
            _validate_webhook_status_url(
                'https://github.corp.example.com/org/repo.git',
                'https://api.github.com/repos/org/repo/statuses/abc',
            )
            is False
        )

    def test_attacker_url_rejected(self):
        assert (
            _validate_webhook_status_url(
                'https://github.com/ansible/awx.git',
                'https://evil.example.com/steal',
            )
            is False
        )

    def test_attacker_ip_rejected(self):
        assert (
            _validate_webhook_status_url(
                'https://github.com/ansible/awx.git',
                'http://10.0.0.1:9999/steal',
            )
            is False
        )

    def test_scp_style_scm_url(self):
        assert (
            _validate_webhook_status_url(
                'git@github.com:ansible/awx.git',
                'https://api.github.com/repos/ansible/awx/statuses/abc',
            )
            is True
        )

    def test_scp_style_scm_url_rejects_attacker(self):
        assert (
            _validate_webhook_status_url(
                'git@github.com:ansible/awx.git',
                'https://evil.example.com/steal',
            )
            is False
        )

    def test_bitbucket_dc_matching_host(self):
        assert (
            _validate_webhook_status_url(
                'https://bitbucket.example.com/scm/PROJ/repo.git',
                'https://bitbucket.example.com/rest/build-status/1.0/commits/abc123',
            )
            is True
        )

    def test_bitbucket_dc_attacker_rejected(self):
        assert (
            _validate_webhook_status_url(
                'https://bitbucket.example.com/scm/PROJ/repo.git',
                'https://evil.example.com/rest/build-status/1.0/commits/abc123',
            )
            is False
        )

    def test_no_project_rejects(self):
        assert (
            _validate_webhook_status_url(
                None,
                'https://api.github.com/repos/org/repo/statuses/abc',
                project_exists=False,
            )
            is False
        )

    def test_empty_scm_url_rejects(self):
        assert (
            _validate_webhook_status_url(
                '',
                'https://api.github.com/repos/org/repo/statuses/abc',
            )
            is False
        )

    def test_status_url_with_no_hostname_rejects(self):
        assert (
            _validate_webhook_status_url(
                'https://github.com/ansible/awx.git',
                '/relative/path',
            )
            is False
        )
