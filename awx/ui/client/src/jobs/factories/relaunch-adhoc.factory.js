export default
    function RelaunchAdhoc(AdhocRun) {
        return function(params) {
            var scope = params.scope,
                id = params.id;
            AdhocRun({ scope: scope, project_id: id, relaunch: true });
        };
    }

RelaunchAdhoc.$inject =
    [   'AdhocRun'   ];
