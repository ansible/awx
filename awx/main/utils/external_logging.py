import os
import shutil
import tempfile
import urllib.parse as urlparse

from django.conf import settings

from awx.main.utils.reload import supervisor_service_command
from awx.main.dispatch.publish import task


def construct_rsyslog_conf_template(settings=settings):
    tmpl = ''
    parts = []
    enabled = getattr(settings, 'LOG_AGGREGATOR_ENABLED')
    host = getattr(settings, 'LOG_AGGREGATOR_HOST', '')
    port = getattr(settings, 'LOG_AGGREGATOR_PORT', '')
    protocol = getattr(settings, 'LOG_AGGREGATOR_PROTOCOL', '')
    timeout = getattr(settings, 'LOG_AGGREGATOR_TCP_TIMEOUT', 5)
    action_queue_size = getattr(settings, 'LOG_AGGREGATOR_ACTION_QUEUE_SIZE', 131072)
    max_disk_space_action_queue = getattr(settings, 'LOG_AGGREGATOR_ACTION_MAX_DISK_USAGE_GB', 1)
    spool_directory = getattr(settings, 'LOG_AGGREGATOR_MAX_DISK_USAGE_PATH', '/var/lib/awx').rstrip('/')
    error_log_file = getattr(settings, 'LOG_AGGREGATOR_RSYSLOGD_ERROR_LOG_FILE', '')

    queue_options = [
        f'queue.spoolDirectory="{spool_directory}"',
        'queue.filename="awx-external-logger-action-queue"',
        f'queue.maxDiskSpace="{max_disk_space_action_queue}g"',  # overall disk space for all queue files
        'queue.maxFileSize="100m"',  # individual file size
        'queue.type="LinkedList"',
        'queue.saveOnShutdown="on"',
        'queue.syncqueuefiles="on"',  # (f)sync when checkpoint occurs
        'queue.checkpointInterval="1000"',  # Update disk queue every 1000 messages
        f'queue.size="{action_queue_size}"',  # max number of messages in queue
        f'queue.highwaterMark="{int(action_queue_size * 0.75)}"',  # 75% of queue.size
        f'queue.discardMark="{int(action_queue_size * 0.9)}"',  # 90% of queue.size
        'queue.discardSeverity="5"',  # Only discard notice, info, debug if we must discard anything
    ]

    if not os.access(spool_directory, os.W_OK):
        spool_directory = '/var/lib/awx'

    max_bytes = settings.MAX_EVENT_RES_DATA
    if settings.LOG_AGGREGATOR_RSYSLOGD_DEBUG:
        parts.append('$DebugLevel 2')
    parts.extend(
        [
            '$WorkDirectory /var/lib/awx/rsyslog',
            f'$MaxMessageSize {max_bytes}',
            '$IncludeConfig /var/lib/awx/rsyslog/conf.d/*.conf',
            'module(load="imuxsock" SysSock.Use="off")',
            'input(type="imuxsock" Socket="' + settings.LOGGING['handlers']['external_logger']['address'] + '" unlink="on" RateLimit.Burst="0")',
            'template(name="awx" type="string" string="%rawmsg-after-pri%")',
        ]
    )

    def escape_quotes(x):
        return x.replace('"', '\\"')

    if not enabled:
        parts.append('action(type="omfile" file="/dev/null")')  # rsyslog needs *at least* one valid action to start
        tmpl = '\n'.join(parts)
        return tmpl

    if protocol.startswith('http'):
        # urlparse requires '//' to be provided if scheme is not specified
        original_parsed = urlparse.urlsplit(host)
        if (not original_parsed.scheme and not host.startswith('//')) or original_parsed.hostname is None:
            host = 'https://%s' % (host)
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
            f'action.resumeInterval="{timeout}"',
        ] + queue_options
        if error_log_file:
            params.append(f'errorfile="{error_log_file}"')
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
        params = [
            'type="omfwd"',
            f'target="{host}"',
            f'port="{port}"',
            f'protocol="{protocol}"',
            'action.resumeRetryCount="-1"',
            f'action.resumeInterval="{timeout}"',
            'template="awx"',
        ] + queue_options
        params = ' '.join(params)
        parts.append(f'action({params})')

    else:
        parts.append('action(type="omfile" file="/dev/null")')  # rsyslog needs *at least* one valid action to start
    tmpl = '\n'.join(parts)
    return tmpl


@task(queue='rsyslog_configurer')
def reconfigure_rsyslog():
    tmpl = construct_rsyslog_conf_template()
    # Write config to a temp file then move it to preserve atomicity
    with tempfile.TemporaryDirectory(dir='/var/lib/awx/rsyslog/', prefix='rsyslog-conf-') as temp_dir:
        path = temp_dir + '/rsyslog.conf.temp'
        with open(path, 'w') as f:
            os.chmod(path, 0o640)
            f.write(tmpl + '\n')
        shutil.move(path, '/var/lib/awx/rsyslog/rsyslog.conf')
    supervisor_service_command(command='restart', service='awx-rsyslogd')
