from django.conf import settings

from ansible_base.lib.utils.db import get_pg_notify_params
from awx.main.dispatch import get_task_queuename
from awx.main.dispatch.pool import get_auto_max_workers


def get_dispatcherd_config(for_service: bool = False) -> dict:
    """Return a dictionary config for dispatcherd

    Parameters:
    for_service: if True, include dynamic options needed for running the dispatcher service
      this will require database access, you should delay evaluation until after app setup
    """
    config = {
        "version": 2,
        "service": {
            "pool_kwargs": {
                "min_workers": settings.JOB_EVENT_WORKERS,
                "max_workers": get_auto_max_workers(),
            },
            "main_kwargs": {"node_id": settings.CLUSTER_HOST_ID},
            "process_manager_cls": "ForkServerManager",
            "process_manager_kwargs": {"preload_modules": ['awx.main.dispatch.hazmat']},
        },
        "brokers": {
            "pg_notify": {
                "config": get_pg_notify_params(),
                "sync_connection_factory": "ansible_base.lib.utils.db.psycopg_connection_from_django",
                "default_publish_channel": settings.CLUSTER_HOST_ID,  # used for debugging commands
            },
            "socket": {"socket_path": settings.DISPATCHERD_DEBUGGING_SOCKFILE},
        },
        "publish": {
            "default_control_broker": "socket",
            "default_broker": "pg_notify",
        },
        "worker": {"worker_cls": "awx.main.dispatch.worker.dispatcherd.AWXTaskWorker"},
    }

    if for_service:
        config["producers"] = {
            "ScheduledProducer": {"task_schedule": settings.DISPATCHER_SCHEDULE},
            "OnStartProducer": {"task_list": {"awx.main.tasks.system.dispatch_startup": {}}},
            "ControlProducer": {},
        }

        config["brokers"]["pg_notify"]["channels"] = ['tower_broadcast_all', 'tower_settings_change', get_task_queuename()]

    return config
