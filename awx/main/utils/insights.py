# Copyright (c) 2017 Ansible Tower by Red Hat
# All Rights Reserved.


# Old Insights API -> New API
#
# last_check_in -> checked_on
# reports[] -> active_reports[]
# reports[].rule.{description,summary} -> active_reports[].rule.{description,summary}
# reports[].rule.category -> active_reports[].rule.category.name
# reports[].rule.severity (str) -> active_reports[].rule.total_risk (int)

# reports[].rule.{ansible,ansible_fix} appears to be unused
# reports[].maintenance_actions[] missing entirely, will be provided
#   by a different Insights endpoint


def filter_insights_api_response(json):
    severity_mapping = {
        1: 'INFO',
        2: 'WARN',
        3: 'ERROR',
        4: 'CRITICAL'
    }

    new_json = {}
    if 'checked_on' in json:
        new_json['last_check_in'] = json['checked_on']
    if 'active_reports' in json:
        new_json['reports'] = []
        for rep in json['active_reports']:
            new_report = {
                'rule': {},
                'maintenance_actions': []  # This will be populated by a different API call
            }
            rule = rep.get('rule') or {}
            for k in ['description', 'summary']:
                if k in rule:
                    new_report['rule'][k] = rule[k]
            if 'category' in rule:
                new_report['category'] = rule['category']['name']
            if rule.get('total_risk') in severity_mapping:
                new_report['severity'] = severity_mapping[rule['total_risk']]

            new_json['reports'].append(new_report)

    return new_json
