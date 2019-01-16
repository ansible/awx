from django.conf import settings


def get_local_queuename():
    return settings.CLUSTER_HOST_ID
