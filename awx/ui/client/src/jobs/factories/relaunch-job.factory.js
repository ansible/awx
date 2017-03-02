export default
    function RelaunchJob(RelaunchInventory, RelaunchPlaybook, RelaunchSCM, RelaunchAdhoc) {
        return function(params) {
            var scope = params.scope,
                id = params.id,
                type = params.type,
                name = params.name;
            if (type === 'inventory_update') {
                RelaunchInventory({ scope: scope, id: id});
            }
            else if (type === 'ad_hoc_command') {
                RelaunchAdhoc({ scope: scope, id: id, name: name });
            }
            else if (type === 'job' || type === 'system_job' || type === 'workflow_job') {
                RelaunchPlaybook({ scope: scope, id: id, name: name, job_type: type });
            }
            else if (type === 'project_update') {
                RelaunchSCM({ scope: scope, id: id });
            }
        };
    }

RelaunchJob.$inject =
    [   'RelaunchInventory',
        'RelaunchPlaybook',
        'RelaunchSCM',
        'RelaunchAdhoc'
    ];
