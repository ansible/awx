/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', '$rootScope', '$location', '$log',
    '$stateParams', 'Rest', 'Alert', 'Prompt', 'ReturnToCaller', 'ClearScope', 'ProcessErrors',
    'GetBasePath', 'JobTemplateForm', 'InitiatePlaybookRun', 'Wait',
    '$compile', '$state', 'OrgJobTemplateList', 'OrgJobTemplateDataset',
    function($scope, $rootScope, $location, $log,
        $stateParams, Rest, Alert, Prompt, ReturnToCaller, ClearScope, ProcessErrors,
        GetBasePath, JobTemplateForm, InitiatePlaybookRun, Wait,
        $compile, $state, OrgJobTemplateList, Dataset) {

        var list = OrgJobTemplateList,
            orgBase = GetBasePath('organizations');

        $scope.$on(`ws-jobs`, function () {
            // @issue old search
            //$scope.search(list.iterator);
        });

        init();

        function init() {
            // search init
            $scope.list = list;
            $scope[`${list.iterator}_dataset`] = Dataset.data;
            $scope[list.name] = $scope[`${list.iterator}_dataset`].results;
            Rest.setUrl(orgBase + $stateParams.organization_id);
            Rest.get()
                .success(function(data) {
                    $scope.organization_name = data.name;
                    $scope.org_id = data.id;

                    $scope.orgRelatedUrls = data.related;
                });
        }

        $scope.addJobTemplate = function() {
            $state.go('jobTemplates.add');
        };

        $scope.editJobTemplate = function(id) {
            $state.go('jobTemplates.edit', { id: id });
        };

        $scope.submitJob = function(id) {
            InitiatePlaybookRun({ scope: $scope, id: id });
        };

        $scope.scheduleJob = function(id) {
            $state.go('jobTemplateSchedules', { id: id });
        };

        $scope.formCancel = function() {
            $state.go('organizations');
        };

    }
];
