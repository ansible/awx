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
    GetBasePath, Rest, ProcessErrors, Empty, GetChoices, LookUpName,
    ParseTypeChange, ParseVariableString, DeleteJob, Wait, i18n,
    fieldChoices, fieldLabels, Project, Alert, InventorySource,
    jobData) {

    var job_id = $stateParams.id,
        jobType = $state.current.data.jobType;

    // This scope variable controls whether or not the left panel is shown and the right panel
    // is expanded to take up the full screen
    $scope.stdoutFullScreen = false;
    $scope.toggleStdoutFullscreenTooltip = i18n._("Expand Output");

    $scope.explanationLimit = 150;

    // Listen for job status updates that may come across via sockets.  We need to check the payload
    // to see whethere the updated job is the one that we're currently looking at.
    $scope.$on(`ws-jobs`, function(e, data) {
        if (parseInt(data.unified_job_id, 10) === parseInt(job_id,10) && $scope.job) {
            $scope.job.status = data.status;
        }

        if (data.status === 'failed' || data.status === 'canceled' || data.status === 'error' || data.status === 'successful') {
            // Go out and refresh the job details

            Rest.setUrl(GetBasePath('base') + jobType + '/' + job_id + '/');
            Rest.get()
                .then(({data}) => {
                    updateJobObj(data);
                });
        }
    });

    $scope.previousTaskFailed = false;

    $scope.$watch('job.job_explanation', function(explanation) {
        if (explanation && explanation.split(":")[0] === "Previous Task Failed") {
            $scope.previousTaskFailed = true;

            var taskObj = JSON.parse(explanation.substring(explanation.split(":")[0].length + 1));
            // return a promise from the options request with the permission type choices (including adhoc) as a param
            var fieldChoice = fieldChoices({
                $scope: $scope,
                url: GetBasePath('unified_jobs'),
                field: 'type'
            });

            // manipulate the choices from the options request to be set on
            // scope and be usable by the list form
            fieldChoice.then(function (choices) {
                choices =
                    fieldLabels({
                        choices: choices
                    });
                $scope.explanation_fail_type = choices[taskObj.job_type];
                $scope.explanation_fail_name = taskObj.job_name;
                $scope.explanation_fail_id = taskObj.job_id;
                $scope.task_detail = $scope.explanation_fail_type + " failed for " + $scope.explanation_fail_name + " with ID " + $scope.explanation_fail_id + ".";
            });
        } else {
            $scope.previousTaskFailed = false;
        }
    });

    // Set the parse type so that CodeMirror knows how to display extra params YAML/JSON
    $scope.parseType = 'yaml';

    function updateJobObj(updatedJobData) {

        // Go out and get the job details based on the job type.  jobType gets defined
        // in the data block of the route declaration for each of the different types
        // of stdout jobs.

        $scope.job = updatedJobData;
        $scope.job_template_name = updatedJobData.name;
        $scope.created_by = updatedJobData.summary_fields.created_by;
        $scope.project_name = (updatedJobData.summary_fields.project) ? updatedJobData.summary_fields.project.name : '';
        $scope.inventory_name = (updatedJobData.summary_fields.inventory) ? updatedJobData.summary_fields.inventory.name : '';
        $scope.job_template_url = '/#/templates/' + updatedJobData.unified_job_template;
        if($scope.inventory_name && updatedJobData.inventory && updatedJobData.summary_fields.inventory && updatedJobData.summary_fields.inventory.kind) {
            if(updatedJobData.summary_fields.inventory.kind === '') {
                $scope.inventory_url = '/#/inventories/inventory' + updatedJobData.inventory;
            }
            else if(updatedJobData.summary_fields.inventory.kind === 'smart') {
                $scope.inventory_url = '/#/inventories/smart_inventory' + updatedJobData.inventory;
            }
        }
        else {
            $scope.inventory_url = '';
        }
        $scope.project_url = ($scope.project_name && updatedJobData.project) ? '/#/projects/' + updatedJobData.project : '';
        $scope.credential_name = (updatedJobData.summary_fields.credential) ? updatedJobData.summary_fields.credential.name : '';
        $scope.credential_url = (updatedJobData.credential) ? '/#/credentials/' + updatedJobData.credential : '';
        $scope.cloud_credential_url = (updatedJobData.cloud_credential) ? '/#/credentials/' + updatedJobData.cloud_credential : '';
        if(updatedJobData.summary_fields && updatedJobData.summary_fields.source_workflow_job &&
            updatedJobData.summary_fields.source_workflow_job.id){
                $scope.workflow_result_link = `/#/workflows/${updatedJobData.summary_fields.source_workflow_job.id}`;
        }
        $scope.playbook = updatedJobData.playbook;
        $scope.credential = updatedJobData.credential;
        $scope.cloud_credential = updatedJobData.cloud_credential;
        $scope.forks = updatedJobData.forks;
        $scope.limit = updatedJobData.limit;
        $scope.verbosity = updatedJobData.verbosity;
        $scope.job_tags = updatedJobData.job_tags;
        $scope.job.module_name = updatedJobData.module_name;
        if (updatedJobData.extra_vars) {
            $scope.variables = ParseVariableString(updatedJobData.extra_vars);
        }

        $scope.$on('getInventorySource', function(e, d) {
            $scope.inv_manage_group_link = '/#/inventories/inventory/' + d.inventory + '/inventory_sources/edit/' + d.id;
        });

        // If we have a source then we have to go get the source choices from the server
        if (!Empty(updatedJobData.source)) {
            if ($scope.removeChoicesReady) {
                $scope.removeChoicesReady();
            }
            $scope.removeChoicesReady = $scope.$on('ChoicesReady', function() {
                $scope.source_choices.every(function(e) {
                    if (e.value === updatedJobData.source) {
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
        if (!Empty(updatedJobData.credential)) {
            LookUpName({
                scope: $scope,
                scope_var: 'credential',
                url: GetBasePath('credentials') + updatedJobData.credential + '/',
                ignore_403: true
            });
        }

        if (!Empty(updatedJobData.inventory)) {
            LookUpName({
                scope: $scope,
                scope_var: 'inventory',
                url: GetBasePath('inventory') + updatedJobData.inventory + '/'
            });
        }

        if (!Empty(updatedJobData.project)) {
            LookUpName({
                scope: $scope,
                scope_var: 'project',
                url: GetBasePath('projects') + updatedJobData.project + '/'
            });
        }

        if (!Empty(updatedJobData.cloud_credential)) {
            LookUpName({
                scope: $scope,
                scope_var: 'cloud_credential',
                url: GetBasePath('credentials') + updatedJobData.cloud_credential + '/',
                ignore_403: true
            });
        }

        if (!Empty(updatedJobData.inventory_source)) {
            LookUpName({
                scope: $scope,
                scope_var: 'inventory_source',
                url: GetBasePath('inventory_sources') + updatedJobData.inventory_source + '/',
                callback: 'getInventorySource'
            });
        }

        if (updatedJobData.extra_vars) {
            ParseTypeChange({
                scope: $scope,
                field_id: 'pre-formatted-variables',
                readOnly: true
            });
        }

        // If the job isn't running we want to clear out the interval that goes out and checks for stdout updates.
        // This interval is defined in the standard out log directive controller.
        if (updatedJobData.status === 'successful' || updatedJobData.status === 'failed' || updatedJobData.status === 'error' || updatedJobData.status === 'canceled') {
            if ($rootScope.jobStdOutInterval) {
                window.clearInterval($rootScope.jobStdOutInterval);
            }
        }

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

        if ($scope.stdoutFullScreen === true) {
            $scope.toggleStdoutFullscreenTooltip = i18n._("Collapse Output");
        } else if ($scope.stdoutFullScreen === false) {
            $scope.toggleStdoutFullscreenTooltip = i18n._("Expand Output");
        }
    };

    $scope.deleteJob = function() {
        DeleteJob({
            scope: $scope,
            id: $scope.job.id,
            job: $scope.job,
            callback: 'DeleteFinished'
        });
    };

    updateJobObj(jobData);

}

JobStdoutController.$inject = [ '$rootScope', '$scope', '$state',
    '$stateParams', 'GetBasePath', 'Rest', 'ProcessErrors',
    'Empty', 'GetChoices',  'LookUpName', 'ParseTypeChange',
    'ParseVariableString', 'DeleteJob', 'Wait', 'i18n',
    'fieldChoices', 'fieldLabels', 'ProjectModel', 'Alert', 'InventorySourceModel',
    'jobData'];
