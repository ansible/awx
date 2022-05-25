#!/usr/bin/python
from .awx_request import get_awx_resources

def get_notifications_by_unified_job_template(unified_job_template_type, unified_job_template_id, notification_type, acc_notifications, awx_auth):
    notifications = get_awx_resources(uri='/api/v2/' + unified_job_template_type + '/' + str(unified_job_template_id) + '/' + notification_type + '/', previousPageResults=[], awx_auth=awx_auth)
    notification_names = []
    for notification in notifications:
        acc_notifications[notification['name']] = notification
        notification_names.append(notification['name'])
    return acc_notifications, notification_names