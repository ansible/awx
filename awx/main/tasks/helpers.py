from django.utils.timezone import now
from rest_framework.fields import DateTimeField


def is_run_threshold_reached(setting, threshold_seconds):
    last_time = DateTimeField().to_internal_value(setting.value) if setting and setting.value else DateTimeField().to_internal_value('1970-01-01T00:00')

    return (now() - last_time).total_seconds() > threshold_seconds
