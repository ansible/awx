#!/usr/bin/python

from .awx_request import get_awx_resources
from .export_tools import parse_extra_vars_to_json

def get_schedules(unified_job_template, awx_auth):
    schedules = get_awx_resources(uri='/api/v2/schedules/?unified_job_template='+str(unified_job_template['id']), previousPageResults=[], awx_auth=awx_auth)
    for schedule_index, schedule_item in enumerate(schedules):
        schedules[schedule_index]['extra_data'] = parse_extra_vars_to_json(schedule_item['extra_data'])
    return schedules