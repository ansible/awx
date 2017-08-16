# Copyright (c) 2017 Ansible Tower by Red Hat
# All Rights Reserved.


def filter_insights_api_response(json):
    new_json = {}
    '''
    'last_check_in',
    'reports.[].rule.severity',
    'reports.[].rule.description',
    'reports.[].rule.category',
    'reports.[].rule.summary',
    'reports.[].rule.ansible_fix',
    'reports.[].rule.ansible',
    'reports.[].maintenance_actions.[].maintenance_plan.name',
    'reports.[].maintenance_actions.[].maintenance_plan.maintenance_id',
    '''

    if 'last_check_in' in json:
        new_json['last_check_in'] = json['last_check_in']
    if 'reports' in json:
        new_json['reports'] = []
        for rep in json['reports']:
            new_report = {
                'rule': {},
                'maintenance_actions': []
            }
            if 'rule' in rep:
                for k in ['severity', 'description', 'category', 'summary', 'ansible_fix', 'ansible',]:
                    if k in rep['rule']:
                        new_report['rule'][k] = rep['rule'][k]

            for action in rep.get('maintenance_actions', []):
                new_action = {'maintenance_plan': {}}
                if 'maintenance_plan' in action:
                    for k in ['name', 'maintenance_id']:
                        if k in action['maintenance_plan']:
                            new_action['maintenance_plan'][k] = action['maintenance_plan'][k]
                new_report['maintenance_actions'].append(new_action)
            
            new_json['reports'].append(new_report)
    return new_json
        
