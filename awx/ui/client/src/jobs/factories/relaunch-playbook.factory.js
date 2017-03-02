export default
    function RelaunchPlaybook(InitiatePlaybookRun) {
        return function(params) {
            var scope = params.scope,
                id = params.id,
                job_type = params.job_type;
            InitiatePlaybookRun({ scope: scope, id: id, relaunch: true, job_type: job_type });
        };
    }

RelaunchPlaybook.$inject =
    [   'InitiatePlaybookRun'   ];
