from django.conf import settings

from ansible_base.lib.utils.db import get_pg_notify_params
from awx.main.dispatch import get_task_queuename
from awx.main.utils.common import get_auto_max_workers


def get_dispatcherd_config(for_service: bool = False, mock_publish: bool = False) -> dict:
    """Return a dictionary config for dispatcherd

    Parameters:
    for_service: if True, include dynamic options needed for running the dispatcher service
      this will require database access, you should delay evaluation until after app setup
    mock_publish: if True, use mock values that don't require database access
      this is used during tests to avoid database queries during app initialization
    """
    # When mock_publish=True (e.g., during tests), use a default value to avoid
    # database access in get_auto_max_workers() which queries settings.IS_K8S
    if mock_publish:
        max_workers = 20  # Reasonable default for tests
    else:
        max_workers = get_auto_max_workers()

    config = {
        "version": 2,
        "service": {
            "pool_kwargs": {
                "min_workers": settings.JOB_EVENT_WORKERS,
                "max_workers": max_workers,
                # This must be less than max_workers to make sense, which is usually 4
                # With reserve of 1, after a burst of tasks, load needs to down to 4-1=3
                # before we return to min_workers
                "scaledown_reserve": 1,
                "worker_max_lifetime_seconds": settings.WORKER_MAX_LIFETIME_SECONDS,
            },
            "main_kwargs": {"node_id": settings.CLUSTER_HOST_ID},
            "process_manager_cls": "ForkServerManager",
            "process_manager_kwargs": {"preload_modules": ['awx.main.dispatch.prefork']},
        },
        "brokers": {},
        "publish": {},
        "worker": {"worker_cls": "awx.main.dispatch.worker.dispatcherd.AWXTaskWorker"},
    }

    if mock_publish:
        config["brokers"]["dispatcherd.testing.brokers.noop"] = {}
        config["publish"]["default_broker"] = "dispatcherd.testing.brokers.noop"
    else:
        config["brokers"]["pg_notify"] = {
            "config": get_pg_notify_params(),
            "sync_connection_factory": "ansible_base.lib.utils.db.psycopg_connection_from_django",
            "default_publish_channel": settings.CLUSTER_HOST_ID,  # used for debugging commands
        }
        config["publish"]["default_broker"] = "pg_notify"

    if for_service:
        config["producers"] = {
            "ScheduledProducer": {"task_schedule": settings.DISPATCHER_SCHEDULE},
            "OnStartProducer": {"task_list": {"awx.main.tasks.system.dispatch_startup": {}}},
            "ControlProducer": {},
        }

        config["brokers"]["pg_notify"]["channels"] = ['tower_broadcast_all', 'tower_settings_change', get_task_queuename()]
        metrics_cfg = settings.METRICS_SUBSYSTEM_CONFIG.get('server', {}).get(settings.METRICS_SERVICE_DISPATCHER)
        if metrics_cfg:
            config["service"]["metrics_kwargs"] = {
                "host": metrics_cfg.get("host", "localhost"),
                "port": metrics_cfg.get("port", 8015),
            }

    return config
