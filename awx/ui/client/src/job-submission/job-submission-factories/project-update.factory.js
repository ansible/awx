export default
    function ProjectUpdate(PromptForPasswords, LaunchJob, Rest, $location, GetBasePath, ProcessErrors, Alert, Wait) {
        return function (params) {
            var scope = params.scope,
            project_id = params.project_id,
            url = GetBasePath('projects') + project_id + '/update/',
            project;

            if (scope.removeUpdateSubmitted) {
                scope.removeUpdateSubmitted();
            }
            scope.removeUpdateSubmitted = scope.$on('UpdateSubmitted', function() {
                // Refresh the project list after update request submitted
                Wait('stop');
                if (/\d$/.test($location.path())) {
                    //Request submitted from projects/N page. Navigate back to the list so user can see status
                    $location.path('/projects');
                }
                if (scope.socketStatus === 'error') {
                    Alert('Update Started', '<div>The request to start the SCM update process was submitted. ' +
                    'To monitor the update status, refresh the page by clicking the <i class="fa fa-refresh"></i> button.</div>', 'alert-info', null, null, null, null, true);
                    if (scope.refresh) {
                        scope.refresh();
                    }
                }
            });

            if (scope.removeStartTheUpdate) {
                scope.removeStartTheUpdate();
            }
            scope.removeStartTheUpdate = scope.$on('StartTheUpdate', function(e, passwords) {
                LaunchJob({ scope: scope, url: url, passwords: passwords, callback: 'UpdateSubmitted' });
            });

            // Check to see if we have permission to perform the update and if any passwords are needed
            Wait('start');
            Rest.setUrl(url);
            Rest.get()
            .then(({data}) => {
                project = data;
                if (project.can_update) {
                    scope.$emit('StartTheUpdate', {});
                }
                else {
                    Alert('Permission Denied', 'You do not have access to update this project. Please contact your system administrator.',
                    'alert-danger');
                }
            })
            .catch(({data, status}) => {
                ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                msg: 'Failed to lookup project ' + url + ' GET returned: ' + status });
            });
        };
    }

ProjectUpdate.$inject =
    [   'PromptForPasswords',
        'LaunchJob',
        'Rest',
        '$location',
        'GetBasePath',
        'ProcessErrors',
        'Alert',
        'Wait'
    ];
