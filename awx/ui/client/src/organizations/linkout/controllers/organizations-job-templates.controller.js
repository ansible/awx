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

        $scope.$on(`${list.iterator}_options`, function(event, data){
            $scope.options = data.data.actions.GET;
            optionsRequestDataProcessing();
        });

        $scope.$watchCollection(`${$scope.list.name}`, function() {
                optionsRequestDataProcessing();
            }
        );
        // iterate over the list and add fields like type label, after the
        // OPTIONS request returns, or the list is sorted/paginated/searched
        function optionsRequestDataProcessing(){
            $scope[list.name].forEach(function(item, item_idx) {
                var itm = $scope[list.name][item_idx];

                // Set the item type label
                if (list.fields.type && $scope.options && $scope.options.hasOwnProperty('type')) {
                    $scope.options.type.choices.every(function(choice) {
                        if (choice[0] === item.type) {
                            itm.type_label = choice[1];
                            return false;
                        }
                        return true;
                    });
                }
            });
        }

        $scope.addJobTemplate = function() {
            $state.go('jobTemplates.add');
        };

        $scope.editJobTemplate = function(id) {
            $state.go('jobTemplates.edit', { id: id });
        };

        $scope.submitJob = function(id) {
            InitiatePlaybookRun({ scope: $scope, id: id, job_type: 'job_template' });
        };

        $scope.scheduleJob = function(id) {
            $state.go('jobTemplateSchedules', { id: id });
        };

        $scope.formCancel = function() {
            $state.go('organizations');
        };

    }
];
