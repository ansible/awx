from django.utils.timezone import now
from rest_framework.fields import DateTimeField


def is_run_threshold_reached(setting, threshold_seconds):
    last_time = DateTimeField().to_internal_value(setting) if setting else None
    if not last_time:
        return True
    else:
        return (now() - last_time).total_seconds() > threshold_seconds
