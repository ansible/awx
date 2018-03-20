/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/**
 * @ngdoc function
 * @name controllers.function:Jobs
 * @description This controller's for the jobs page
 */

 export default ['$state', '$rootScope', '$scope', '$stateParams',
     'Find', 'DeleteJob',
     'GetBasePath', 'Dataset', 'QuerySet', 'ListDefinition', '$interpolate',
     'WorkflowJobModel', 'ProjectModel', 'Alert', 'InventorySourceModel',
     'AdHocCommandModel', 'JobModel',
     function($state, $rootScope, $scope, $stateParams,
         Find, DeleteJob,
         GetBasePath, Dataset, qs, ListDefinition, $interpolate,
         WorkflowJob, Project, Alert, InventorySource,
         AdHocCommand, Job) {

    var list = ListDefinition;

    init();

    function init() {
        // search init
        $scope.list = list;
        $scope[`${list.iterator}_dataset`] = Dataset.data;
        $scope[list.name] = $scope[`${list.iterator}_dataset`].results;

        $scope.showJobType = true;
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

        if($scope[list.name] && $scope[list.name].length > 0) {
            $scope[list.name].forEach(function(item, item_idx) {
                var itm = $scope[list.name][item_idx];

                switch (item.type) {
                    case 'job':
                        item.linkToDetails = `jobResult({id: ${item.id}})`;
                        break;
                    case 'ad_hoc_command':
                        item.linkToDetails = `adHocJobStdout({id: ${item.id}})`;
                        break;
                    case 'system_job':
                        item.linkToDetails = `managementJobStdout({id: ${item.id}})`;
                        break;
                    case 'project_update':
                        item.linkToDetails = `scmUpdateStdout({id: ${item.id}})`;
                        break;
                    case 'inventory_update':
                        item.linkToDetails = `inventorySyncStdout({id: ${item.id}})`;
                        break;
                    case 'workflow_job':
                        item.linkToDetails = `workflowResults({id: ${item.id}})`;
                        break;
                }

                if(item.summary_fields && item.summary_fields.source_workflow_job &&
                    item.summary_fields.source_workflow_job.id){
                        item.workflow_result_link = `/#/workflows/${item.summary_fields.source_workflow_job.id}`;
                }

                // Set the item type label
                if (list.fields.type && $scope.options &&
                        $scope.options.hasOwnProperty('type')) {
                            $scope.options.type.choices.forEach(function(choice) {
                                if (choice[0] === item.type) {
                                itm.type_label = choice[1];
                            }
                        });
                    }
                    buildTooltips(itm);
            });
        }
    }
    function buildTooltips(job) {
        job.status_tip = 'Job ' + job.status + ". Click for details.";
    }

    $scope.deleteJob = function(id) {
        DeleteJob({ scope: $scope, id: id });
    };

    $scope.viewjobResults = function(job) {

        var goTojobResults = function(state) {
            $state.go(state, { id: job.id }, { reload: true });
        };
        switch (job.type) {
            case 'job':
                goTojobResults('jobResult');
                break;
            case 'ad_hoc_command':
                goTojobResults('adHocJobStdout');
                break;
            case 'system_job':
                goTojobResults('managementJobStdout');
                break;
            case 'project_update':
                goTojobResults('scmUpdateStdout');
                break;
            case 'inventory_update':
                goTojobResults('inventorySyncStdout');
                break;
            case 'workflow_job':
                goTojobResults('workflowResults');
                break;
        }

    };

    $scope.$on('ws-jobs', function(){
        let path;
        if (GetBasePath(list.basePath) || GetBasePath(list.name)) {
            path = GetBasePath(list.basePath) || GetBasePath(list.name);
        } else {
            // completed jobs base path involves $stateParams
            let interpolator = $interpolate(list.basePath);
            path = interpolator({ $rootScope: $rootScope, $stateParams: $stateParams });
        }
        qs.search(path, $state.params[`${list.iterator}_search`])
        .then(function(searchResponse) {
            $scope[`${list.iterator}_dataset`] = searchResponse.data;
            $scope[list.name] = $scope[`${list.iterator}_dataset`].results;
        });
    });

    $scope.$on('ws-schedules', function(){
        $state.reload();
    });
}];
