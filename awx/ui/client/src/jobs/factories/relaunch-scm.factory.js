export default
    function RelaunchSCM(ProjectUpdate) {
        return function(params) {
            var scope = params.scope,
                id = params.id;
            ProjectUpdate({ scope: scope, project_id: id });
        };
    }

RelaunchSCM.$inject =
    [   'ProjectUpdate'   ];
