import psutil

from django.conf import settings

from awx.main.utils.common import convert_mem_str_to_bytes, get_mem_effective_capacity


def get_max_workers(max_workers=None, **kwargs):
    if max_workers:
        return max_workers

    settings_absmem = getattr(settings, 'SYSTEM_TASK_ABS_MEM', None)
    if settings_absmem is not None:
        # There are 1073741824 bytes in a gigabyte. Convert bytes to gigabytes by dividing by 2**30
        total_memory_gb = convert_mem_str_to_bytes(settings_absmem) // 2**30
    else:
        total_memory_gb = (psutil.virtual_memory().total >> 30) + 1  # noqa: round up

    # Get same number as max forks based on memory, this function takes memory as bytes
    new_max_workers = get_mem_effective_capacity(total_memory_gb * 2**30)

    # add magic prime number of extra workers to ensure
    # we have a few extra workers to run the heartbeat
    new_max_workers += 7

    # max workers can't be less than min_workers
    new_max_workers = max(settings.JOB_EVENT_WORKERS, new_max_workers)

    return new_max_workers
