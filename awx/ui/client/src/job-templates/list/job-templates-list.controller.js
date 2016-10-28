/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', '$rootScope', '$location', '$stateParams', 'Rest', 'Alert',
    'JobTemplateList', 'Prompt', 'ClearScope', 'ProcessErrors', 'GetBasePath',
    'InitiatePlaybookRun', 'Wait', '$state', '$filter', 'Dataset', 'rbacUiControlService',
    function(
        $scope, $rootScope, $location, $stateParams, Rest, Alert,
        JobTemplateList, Prompt, ClearScope, ProcessErrors, GetBasePath,
        InitiatePlaybookRun, Wait, $state, $filter, Dataset, rbacUiControlService
    ) {
        ClearScope();

        var list = JobTemplateList,
            defaultUrl = GetBasePath('job_templates');

        init();

        function init() {
            $scope.canAdd = false;

            rbacUiControlService.canAdd("job_templates")
                .then(function(canAdd) {
                    $scope.canAdd = canAdd;
                });
            // search init
            $scope.list = list;
            $scope[`${list.iterator}_dataset`] = Dataset.data;
            $scope[list.name] = $scope[`${list.iterator}_dataset`].results;

            $rootScope.flashMessage = null;
        }

        $scope.$on(`ws-jobs`, function () {
            // @issue - this is ham-fisted, expose a simple QuerySet.reload() fn that'll re-fetch dataset
            $state.reload();
        });
        $scope.addJobTemplate = function() {
            $state.go('jobTemplates.add');
        };

        $scope.editJobTemplate = function(id) {
            $state.go('jobTemplates.edit', { job_template_id: id });
        };

        $scope.deleteJobTemplate = function(id, name) {
            var action = function() {
                $('#prompt-modal').modal('hide');
                Wait('start');
                var url = defaultUrl + id + '/';
                Rest.setUrl(url);
                Rest.destroy()
                    .success(function() {
                        $state.go('^', null, { reload: true });
                    })
                    .error(function(data) {
                        Wait('stop');
                        ProcessErrors($scope, data, status, null, {
                            hdr: 'Error!',
                            msg: 'Call to ' + url + ' failed. DELETE returned status: ' + status
                        });
                    });
            };

            Prompt({
                hdr: 'Delete',
                body: '<div class="Prompt-bodyQuery">Are you sure you want to delete the job template below?</div><div class="Prompt-bodyTarget">' + $filter('sanitize')(name) + '</div>',
                action: action,
                actionText: 'DELETE'
            });
        };

        $scope.submitJob = function(id) {
            InitiatePlaybookRun({ scope: $scope, id: id });
        };

        $scope.scheduleJob = function(id) {
            $state.go('jobTemplateSchedules', { id: id });
        };
    }
];
