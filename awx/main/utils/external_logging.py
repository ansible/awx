import urllib.parse as urlparse

from django.conf import settings

from awx.main.utils.reload import supervisor_service_command


def reconfigure_rsyslog():
    tmpl = ''
    if settings.LOG_AGGREGATOR_ENABLED:
        host = getattr(settings, 'LOG_AGGREGATOR_HOST', '')
        port = getattr(settings, 'LOG_AGGREGATOR_PORT', '')
        protocol = getattr(settings, 'LOG_AGGREGATOR_PROTOCOL', '')

        if protocol.startswith('http'):
            scheme = 'https'
            # urlparse requires '//' to be provided if scheme is not specified
            original_parsed = urlparse.urlsplit(host)
            if (not original_parsed.scheme and not host.startswith('//')) or original_parsed.hostname is None:
                host = '%s://%s' % (scheme, host) if scheme else '//%s' % host
            parsed = urlparse.urlsplit(host)

            host = parsed.hostname
            try:
                port = parsed.port or settings.LOG_AGGREGATOR_PORT
            except ValueError:
                port = settings.LOG_AGGREGATOR_PORT

        parts = []
        parts.extend([
            '$ModLoad imudp',
            '$UDPServerRun 51414',
            'template(name="awx" type="string" string="%msg%")',
        ])
        if protocol.startswith('http'):
            # https://github.com/rsyslog/rsyslog-doc/blob/master/source/configuration/modules/omhttp.rst
            ssl = "on" if parsed.scheme == 'https' else "off"
            skip_verify = "off" if settings.LOG_AGGREGATOR_VERIFY_CERT else "on"
            params = [
                'type="omhttp"',
                f'server="{host}"',
                f'serverport="{port}"',
                f'usehttps="{ssl}"',
                f'skipverifyhost="{skip_verify}"',
                'action.resumeRetryCount="-1"',
                'template="awx"',
                'errorfile="/var/log/tower/external.err"',
            ]
            username = getattr(settings, 'LOG_AGGREGATOR_USERNAME', '')
            password = getattr(settings, 'LOG_AGGREGATOR_PASSWORD', '')
            if username:
                params.append(f'uid="{username}"')
            if password:
                params.append(f'pwd="{password}"')
            params = ' '.join(params)
            parts.extend(['module(load="omhttp")', f'action({params})'])
        else:
            parts.append(
                f'action(type="omfwd" target="{host}" port="{port}" protocol="{protocol}" action.resumeRetryCount="-1" template="awx")'  # noqa
            )
        tmpl = '\n'.join(parts)

    with open('/var/lib/awx/rsyslog.conf', 'w') as f:
        f.write(tmpl + '\n')
    supervisor_service_command(command='restart', service='awx-rsyslogd')
