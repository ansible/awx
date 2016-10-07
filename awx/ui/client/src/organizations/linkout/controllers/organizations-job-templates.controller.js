/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', '$rootScope', '$location', '$log',
    '$stateParams', 'Rest', 'Alert', 'JobTemplateList', 'generateList',
    'Prompt', 'SearchInit', 'PaginateInit', 'ReturnToCaller', 'ClearScope',
    'ProcessErrors', 'GetBasePath', 'JobTemplateForm', 'CredentialList',
    'LookUpInit', 'InitiatePlaybookRun', 'Wait', '$compile',
    '$state',
    function($scope, $rootScope, $location, $log,
    $stateParams, Rest, Alert, JobTemplateList, GenerateList, Prompt,
    SearchInit, PaginateInit, ReturnToCaller, ClearScope, ProcessErrors,
    GetBasePath, JobTemplateForm, CredentialList, LookUpInit, InitiatePlaybookRun,
    Wait, $compile, $state) {

        var list,
            jobTemplateUrl,
            generator = GenerateList,
            orgBase = GetBasePath('organizations');

        $scope.$on(`ws-jobs`, function () {
            $scope.search(list.iterator);
        });

        Rest.setUrl(orgBase + $stateParams.organization_id);
        Rest.get()
            .success(function (data) {
                // include name of item in listTitle
                var listTitle = data.name + "<div class='List-titleLockup'></div>JOB TEMPLATES";

                $scope.$parent.activeCard = parseInt($stateParams.organization_id);
                $scope.$parent.activeMode = 'job_templates';
                $scope.organization_name = data.name;
                $scope.org_id = data.id;

                list = _.cloneDeep(JobTemplateList);
                list.emptyListText = "This list is populated by job templates added from the&nbsp;<a ui-sref='jobTemplates.add'>Job Templates</a>&nbsp;section";
                delete list.actions.add;
                delete list.fieldActions.delete;
                jobTemplateUrl = "/api/v1/job_templates/?project__organization=" + data.id;
                list.listTitle = listTitle;
                list.basePath = jobTemplateUrl;

                $scope.orgRelatedUrls = data.related;

                generator.inject(list, { mode: 'edit', scope: $scope, cancelButton: true });

                if ($scope.removePostRefresh) {
                    $scope.removePostRefresh();
                }
                $scope.removePostRefresh = $scope.$on('PostRefresh', function () {
                    // Cleanup after a delete
                    Wait('stop');
                    $('#prompt-modal').modal('hide');
                });

                SearchInit({
                    scope: $scope,
                    set: 'job_templates',
                    list: list,
                    url: jobTemplateUrl
                });
                PaginateInit({
                    scope: $scope,
                    list: list,
                    url: jobTemplateUrl
                });
                $scope.search(list.iterator);
            });

        $scope.addJobTemplate = function () {
            $state.transitionTo('jobTemplates.add');
        };

        $scope.editJobTemplate = function (id) {
            $state.transitionTo('jobTemplates.edit', {id: id});
        };

        $scope.submitJob = function (id) {
            InitiatePlaybookRun({ scope: $scope, id: id });
        };

        $scope.scheduleJob = function (id) {
            $state.go('jobTemplateSchedules', {id: id});
        };

        $scope.formCancel = function(){
            $scope.$parent.activeCard = null;
            $state.go('organizations');
        };

    }
];
