import os

from django.conf import settings


REDIS_GROUP = "tower_settings_change"
RSYSLOG_GROUP = "rsyslog_configurer"
TASK_GROUP = "tower_broadcast_all"
HEARTBEET = "web_heartbeet"


def get_local_queuename():
    return settings.CLUSTER_HOST_ID


def get_control_plane_qs():
    from awx.main.models.ha import Instance

    return Instance.objects.filter(
        node_type__in=(Instance.Types.CONTROL, Instance.Types.HYBRID),
        node_state=Instance.States.READY,
        enabled=True,
    )


def get_task_queuename():
    if os.getenv('AWX_COMPONENT') != 'web':
        return settings.CLUSTER_HOST_ID

    random_task_instance = get_control_plane_qs().only('hostname').order_by('?').first()

    if random_task_instance is None:
        raise ValueError('No task instances are READY and Enabled.')

    return random_task_instance.hostname


def get_all_queues():
    queues = [REDIS_GROUP, RSYSLOG_GROUP, TASK_GROUP, HEARTBEET]
    for instance in get_control_plane_qs():
        queues.append(instance.hostname)
    return queues
