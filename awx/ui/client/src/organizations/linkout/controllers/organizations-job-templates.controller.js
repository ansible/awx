/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', '$rootScope',
    '$stateParams', 'Rest', 'ProcessErrors',
    'GetBasePath', 'Wait',
    '$state', 'OrgJobTemplateList', 'OrgJobTemplateDataset', 'QuerySet',
    function($scope, $rootScope,
        $stateParams, Rest, ProcessErrors,
        GetBasePath, Wait,
        $state, OrgJobTemplateList, Dataset, qs) {

        var list = OrgJobTemplateList,
            orgBase = GetBasePath('organizations');

        $scope.$on(`ws-jobs`, function () {
            let path = GetBasePath(list.basePath) || GetBasePath(list.name);
            qs.search(path, $state.params[`${list.iterator}_search`])
            .then(function(searchResponse) {
                $scope[`${list.iterator}_dataset`] = searchResponse.data;
                $scope[list.name] = $scope[`${list.iterator}_dataset`].results;
            });
        });

        init();

        function init() {
            // search init
            $scope.list = list;
            $scope[`${list.iterator}_dataset`] = Dataset.data;
            $scope[list.name] = $scope[`${list.iterator}_dataset`].results;
            Rest.setUrl(orgBase + $stateParams.organization_id);
            Rest.get()
                .then(({data}) => {
                    $scope.organization_name = data.name;
                    $scope.name = data.name;
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
                    $scope.options.type.choices.forEach(function(choice) {
                        if (choice[0] === item.type) {
                            itm.type_label = choice[1];
                        }
                    });
                }
            });
        }

        $scope.editJobTemplate = function(id) {
            $state.go('templates.editJobTemplate', { job_template_id: id });
        };
    }
];
