import os
import shutil
import tempfile
import urllib.parse as urlparse

from django.conf import settings

from awx.main.utils.reload import supervisor_service_command


def construct_rsyslog_conf_template(settings=settings):
    tmpl = ''
    parts = []
    enabled = getattr(settings, 'LOG_AGGREGATOR_ENABLED')
    host = getattr(settings, 'LOG_AGGREGATOR_HOST', '')
    port = getattr(settings, 'LOG_AGGREGATOR_PORT', '')
    protocol = getattr(settings, 'LOG_AGGREGATOR_PROTOCOL', '')
    timeout = getattr(settings, 'LOG_AGGREGATOR_TCP_TIMEOUT', 5)
    max_disk_space = getattr(settings, 'LOG_AGGREGATOR_MAX_DISK_USAGE_GB', 1)
    spool_directory = getattr(settings, 'LOG_AGGREGATOR_MAX_DISK_USAGE_PATH', '/var/lib/awx').rstrip('/')

    if not os.access(spool_directory, os.W_OK):
        spool_directory = '/var/lib/awx'

    max_bytes = settings.MAX_EVENT_RES_DATA
    if settings.LOG_AGGREGATOR_RSYSLOGD_DEBUG:
        parts.append('$DebugLevel 2')
    parts.extend([
        '$WorkDirectory /var/lib/awx/rsyslog',
        f'$MaxMessageSize {max_bytes}',
        '$IncludeConfig /var/lib/awx/rsyslog/conf.d/*.conf',
        f'main_queue(queue.spoolDirectory="{spool_directory}" queue.maxdiskspace="{max_disk_space}g" queue.type="Disk" queue.filename="awx-external-logger-backlog")',  # noqa
        'module(load="imuxsock" SysSock.Use="off")',
        'input(type="imuxsock" Socket="' + settings.LOGGING['handlers']['external_logger']['address'] + '" unlink="on")',
        'template(name="awx" type="string" string="%rawmsg-after-pri%")',
    ])

    def escape_quotes(x):
        return x.replace('"', '\\"')

    if not enabled:
        parts.append('action(type="omfile" file="/dev/null")')  # rsyslog needs *at least* one valid action to start
        tmpl = '\n'.join(parts)
        return tmpl
        
    if protocol.startswith('http'):
        scheme = 'https'
        # urlparse requires '//' to be provided if scheme is not specified
        original_parsed = urlparse.urlsplit(host)
        if (not original_parsed.scheme and not host.startswith('//')) or original_parsed.hostname is None:
            host = '%s://%s' % (scheme, host) if scheme else '//%s' % host
        parsed = urlparse.urlsplit(host)

        host = escape_quotes(parsed.hostname)
        try:
            if parsed.port:
                port = parsed.port
        except ValueError:
            port = settings.LOG_AGGREGATOR_PORT

        # https://github.com/rsyslog/rsyslog-doc/blob/master/source/configuration/modules/omhttp.rst
        ssl = 'on' if parsed.scheme == 'https' else 'off'
        skip_verify = 'off' if settings.LOG_AGGREGATOR_VERIFY_CERT else 'on'
        allow_unsigned = 'off' if settings.LOG_AGGREGATOR_VERIFY_CERT else 'on'
        if not port:
            port = 443 if parsed.scheme == 'https' else 80

        params = [
            'type="omhttp"',
            f'server="{host}"',
            f'serverport="{port}"',
            f'usehttps="{ssl}"',
            f'allowunsignedcerts="{allow_unsigned}"',
            f'skipverifyhost="{skip_verify}"',
            'action.resumeRetryCount="-1"',
            'template="awx"',
            'errorfile="/var/log/tower/rsyslog.err"',
            f'action.resumeInterval="{timeout}"'
        ]
        if parsed.path:
            path = urlparse.quote(parsed.path[1:], safe='/=')
            if parsed.query:
                path = f'{path}?{urlparse.quote(parsed.query)}'
            params.append(f'restpath="{path}"')
        username = escape_quotes(getattr(settings, 'LOG_AGGREGATOR_USERNAME', ''))
        password = escape_quotes(getattr(settings, 'LOG_AGGREGATOR_PASSWORD', ''))
        if getattr(settings, 'LOG_AGGREGATOR_TYPE', None) == 'splunk':
            # splunk has a weird authorization header <shrug>
            if password:
                # from omhttp docs:
                # https://www.rsyslog.com/doc/v8-stable/configuration/modules/omhttp.html
                # > Currently only a single additional header/key pair is
                # > configurable, further development is needed to support
                # > arbitrary header key/value lists.
                params.append('httpheaderkey="Authorization"')
                params.append(f'httpheadervalue="Splunk {password}"')
        elif username:
            params.append(f'uid="{username}"')
            if password:
                # you can only have a basic auth password if there's a username
                params.append(f'pwd="{password}"')
        params = ' '.join(params)
        parts.extend(['module(load="omhttp")', f'action({params})'])
    elif protocol and host and port:
        parts.append(
            f'action(type="omfwd" target="{host}" port="{port}" protocol="{protocol}" action.resumeRetryCount="-1" action.resumeInterval="{timeout}" template="awx")'  # noqa
        )
    else:
        parts.append('action(type="omfile" file="/dev/null")')  # rsyslog needs *at least* one valid action to start
    tmpl = '\n'.join(parts)
    return tmpl


def reconfigure_rsyslog():
    tmpl = construct_rsyslog_conf_template()
    # Write config to a temp file then move it to preserve atomicity
    with tempfile.TemporaryDirectory(prefix='rsyslog-conf-') as temp_dir:
        path = temp_dir + '/rsyslog.conf.temp'
        with open(path, 'w') as f:
            os.chmod(path, 0o640)
            f.write(tmpl + '\n')
        shutil.move(path, '/var/lib/awx/rsyslog/rsyslog.conf')
    supervisor_service_command(command='restart', service='awx-rsyslogd')
