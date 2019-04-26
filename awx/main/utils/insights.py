# Copyright (c) 2017 Ansible Tower by Red Hat
# All Rights Reserved.


# Old Insights API -> New API
#
# last_check_in is missing entirely, is now provided by a different endpoint
# reports[] -> []
# reports[].rule.{description,summary} -> [].rule.{description,summary}
# reports[].rule.category -> [].rule.category.name
# reports[].rule.severity (str) -> [].rule.total_risk (int)

# reports[].rule.{ansible,ansible_fix} appears to be unused
# reports[].maintenance_actions[] missing entirely, is now provided
#   by a different Insights endpoint


def filter_insights_api_response(platform_info, reports, remediations):
    severity_mapping = {
        1: 'INFO',
        2: 'WARN',
        3: 'ERROR',
        4: 'CRITICAL'
    }

    new_json = {
        'platform_id': platform_info['id'],
        'last_check_in': platform_info.get('updated'),
        'reports': [],
    }
    for rep in reports:
        new_report = {
            'rule': {},
            'maintenance_actions': remediations
        }
        rule = rep.get('rule') or {}
        for k in ['description', 'summary']:
            if k in rule:
                new_report['rule'][k] = rule[k]
        if 'category' in rule:
            new_report['rule']['category'] = rule['category']['name']
        if rule.get('total_risk') in severity_mapping:
            new_report['rule']['severity'] = severity_mapping[rule['total_risk']]

        new_json['reports'].append(new_report)

    return new_json
