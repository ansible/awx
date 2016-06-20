/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/**
 * @ngdoc function
 * @name controllers.function:JobStdout
 * @description This controller's for the standard out page that can be displayed when a job runs
*/

export function JobStdoutController ($rootScope, $scope, $state, $stateParams,
    ClearScope, GetBasePath, Rest, ProcessErrors, Empty, GetChoices, LookUpName,
    ParseTypeChange, ParseVariableString, RelaunchJob, DeleteJob, Wait) {

    ClearScope();

    var job_id = $stateParams.id,
        jobType = $state.current.data.jobType;

    // This scope variable controls whether or not the left panel is shown and the right panel
    // is expanded to take up the full screen
    $scope.stdoutFullScreen = false;

    // Listen for job status updates that may come across via sockets.  We need to check the payload
    // to see whethere the updated job is the one that we're currently looking at.
    if ($scope.removeJobStatusChange) {
        $scope.removeJobStatusChange();
    }
    $scope.removeJobStatusChange = $rootScope.$on('JobStatusChange-jobStdout', function(e, data) {
        if (parseInt(data.unified_job_id, 10) === parseInt(job_id,10) && $scope.job) {
            $scope.job.status = data.status;
        }

        if (data.status === 'failed' || data.status === 'canceled' || data.status === 'error' || data.status === 'successful') {
            // Go out and refresh the job details
            getJobDetails();
        }
    });

    // Set the parse type so that CodeMirror knows how to display extra params YAML/JSON
    $scope.parseType = 'yaml';

    function getJobDetails() {

        // Go out and get the job details based on the job type.  jobType gets defined
        // in the data block of the route declaration for each of the different types
        // of stdout jobs.
        Rest.setUrl(GetBasePath('base') + jobType + '/' + job_id + '/');
        Rest.get()
            .success(function(data) {
                $scope.job = data;
                $scope.job_template_name = data.name;
                $scope.created_by = data.summary_fields.created_by;
                $scope.project_name = (data.summary_fields.project) ? data.summary_fields.project.name : '';
                $scope.inventory_name = (data.summary_fields.inventory) ? data.summary_fields.inventory.name : '';
                $scope.job_template_url = '/#/job_templates/' + data.unified_job_template;
                $scope.inventory_url = ($scope.inventory_name && data.inventory) ? '/#/inventories/' + data.inventory : '';
                $scope.project_url = ($scope.project_name && data.project) ? '/#/projects/' + data.project : '';
                $scope.credential_name = (data.summary_fields.credential) ? data.summary_fields.credential.name : '';
                $scope.credential_url = (data.credential) ? '/#/credentials/' + data.credential : '';
                $scope.cloud_credential_url = (data.cloud_credential) ? '/#/credentials/' + data.cloud_credential : '';
                $scope.playbook = data.playbook;
                $scope.credential = data.credential;
                $scope.cloud_credential = data.cloud_credential;
                $scope.forks = data.forks;
                $scope.limit = data.limit;
                $scope.verbosity = data.verbosity;
                $scope.job_tags = data.job_tags;
                if (data.extra_vars) {
                    $scope.variables = ParseVariableString(data.extra_vars);
                }

                // If we have a source then we have to go get the source choices from the server
                if (!Empty(data.source)) {
                    if ($scope.removeChoicesReady) {
                        $scope.removeChoicesReady();
                    }
                    $scope.removeChoicesReady = $scope.$on('ChoicesReady', function() {
                        $scope.source_choices.every(function(e) {
                            if (e.value === data.source) {
                                $scope.source = e.label;
                                return false;
                            }
                            return true;
                        });
                    });
                    // GetChoices can be found in the helper: Utilities.js
                    // It attaches the source choices to $scope.source_choices.
                    // Then, when the callback is fired, $scope.source is bound
                    // to the corresponding label.
                    GetChoices({
                        scope: $scope,
                        url: GetBasePath('inventory_sources'),
                        field: 'source',
                        variable: 'source_choices',
                        choice_name: 'choices',
                        callback: 'ChoicesReady'
                    });
                }

                // LookUpName can be found in the lookup-name.factory
                // It attaches the name that it gets (based on the url)
                // to the $scope variable defined by the attribute scope_var.
                if (!Empty(data.credential)) {
                    LookUpName({
                        scope: $scope,
                        scope_var: 'credential',
                        url: GetBasePath('credentials') + data.credential + '/'
                    });
                }

                if (!Empty(data.inventory)) {
                    LookUpName({
                        scope: $scope,
                        scope_var: 'inventory',
                        url: GetBasePath('inventory') + data.inventory + '/'
                    });
                }

                if (!Empty(data.project)) {
                    LookUpName({
                        scope: $scope,
                        scope_var: 'project',
                        url: GetBasePath('projects') + data.project + '/'
                    });
                }

                if (!Empty(data.cloud_credential)) {
                    LookUpName({
                        scope: $scope,
                        scope_var: 'cloud_credential',
                        url: GetBasePath('credentials') + data.cloud_credential + '/'
                    });
                }

                if (!Empty(data.inventory_source)) {
                    LookUpName({
                        scope: $scope,
                        scope_var: 'inventory_source',
                        url: GetBasePath('inventory_sources') + data.inventory_source + '/'
                    });
                }

                if (data.extra_vars) {
                    ParseTypeChange({ scope: $scope, field_id: 'pre-formatted-variables' });
                }

                if ($scope.job.type === 'inventory_update' && !$scope.inv_manage_group_link) {

                    var groupWatcher = $scope.$watch('group', function(group){
                        if(group) {
                            // The group's been set by the LookUpName call on inventory_source
                            var ancestorGroupIds = [];

                            // Remove the watcher
                            groupWatcher();

                            // Function that we'll call recursively to go out and get a groups parent(s)
                            var getGroupParent = function(groupId) {
                                Rest.setUrl(GetBasePath('base') + 'groups/?children__id=' + groupId);
                                Rest.get()
                                    .success(function(data) {
                                        if(data.results && data.results.length > 0) {
                                            ancestorGroupIds.push(data.results[0].id);
                                            // Go get this groups first parent
                                            getGroupParent(data.results[0].id);
                                        }
                                        else {
                                            // We've run out of ancestors to traverse - lets build a link (note that $scope.inventory is
                                            // set in the lookup-name factory just like $scope.group)
                                            $scope.inv_manage_group_link = '/#/inventories/' + $scope.inventory + '/manage';
                                            for(var i=ancestorGroupIds.length; i > 0; i--) {
                                                $scope.inv_manage_group_link += (i === ancestorGroupIds.length ? '?' : '&') + 'group=' + ancestorGroupIds[i-1];
                                            }
                                        }
                                    })
                                    .error(function(data, status) {
                                        ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                                            msg: 'Failed to retrieve group parent(s): ' + groupId + '. GET returned: ' + status });
                                    });
                            };

                            // Trigger the recursive chain of parent group gathering
                            getGroupParent(group);
                        }
                    });
                }

                // If the job isn't running we want to clear out the interval that goes out and checks for stdout updates.
                // This interval is defined in the standard out log directive controller.
                if (data.status === 'successful' || data.status === 'failed' || data.status === 'error' || data.status === 'canceled') {
                    if ($rootScope.jobStdOutInterval) {
                        window.clearInterval($rootScope.jobStdOutInterval);
                    }
                }
            })
            .error(function(data, status) {
                ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                    msg: 'Failed to retrieve job: ' + job_id + '. GET returned: ' + status });
            });

    }

    if ($scope.removeDeleteFinished) {
        $scope.removeDeleteFinished();
    }
    $scope.removeDeleteFinished = $scope.$on('DeleteFinished', function(e, action) {
        Wait('stop');
        if (action !== 'cancel') {
            Wait('stop');
            $state.go('jobs');
        }
    });

    // TODO: this is currently not used but is necessary for cases where sockets
    // are not available and a manual refresh trigger is needed.
    $scope.refresh = function(){
        $scope.$emit('LoadStdout');
    };

    // Click binding for the expand/collapse button on the standard out log
    $scope.toggleStdoutFullscreen = function() {
        $scope.stdoutFullScreen = !$scope.stdoutFullScreen;
    };

    $scope.deleteJob = function() {
        DeleteJob({
            scope: $scope,
            id: $scope.job.id,
            job: $scope.job,
            callback: 'DeleteFinished'
        });
    };

    $scope.relaunchJob = function() {
        var typeId, job = $scope.job;
        if (job.type === 'inventory_update') {
            typeId = job.inventory_source;
        }
        else if (job.type === 'project_update') {
            typeId = job.project;
        }
        else if (job.type === 'job' || job.type === "system_job" || job.type === 'ad_hoc_command') {
            typeId = job.id;
        }
        RelaunchJob({ scope: $scope, id: typeId, type: job.type, name: job.name });
    };

    getJobDetails();

}

JobStdoutController.$inject = [ '$rootScope', '$scope', '$state',
    '$stateParams', 'ClearScope', 'GetBasePath', 'Rest', 'ProcessErrors',
    'Empty', 'GetChoices',  'LookUpName', 'ParseTypeChange',
    'ParseVariableString', 'RelaunchJob', 'DeleteJob', 'Wait'];
