/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export function PortalModeJobsController($scope, $state, qs, GetBasePath, PortalJobsList, Dataset) {

    var list = PortalJobsList;

    $scope.$on('ws-jobs', function() {
        let path = GetBasePath(list.basePath) || GetBasePath(list.name);
        qs.search(path, $state.params[`${list.iterator}_search`])
        .then(function(searchResponse) {
            $scope[`${list.iterator}_dataset`] = searchResponse.data;
            $scope[list.name] = $scope[`${list.iterator}_dataset`].results;
        });
    });

    init();

    function init(data) {
        let d = (!data) ? Dataset : data;
        // search init
        $scope.list = list;
        $scope[`${list.iterator}_dataset`] = d.data;
        $scope[list.name] = $scope[`${list.iterator}_dataset`].results;

        $scope.iterator = list.iterator;
    }

    $scope.refresh = function() {
        $state.go('.', null, {reload: true});
    };

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
        job.status_tip = `Job ${job.status}. Click for details.`;
    }

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
}

PortalModeJobsController.$inject = ['$scope', '$state', 'QuerySet', 'GetBasePath', 'PortalJobsList', 'jobsDataset'];
