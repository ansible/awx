export default ['$scope', 'InstanceGroupList', 'GetBasePath', 'Rest', 'Dataset','Find', '$state', '$q',
    function($scope, InstanceGroupList, GetBasePath, Rest, Dataset, Find, $state, $q) {
        let list = InstanceGroupList;

        init();

        function init(){
            $scope.optionsDefer = $q.defer();
            $scope.list = list;
            $scope[`${list.iterator}_dataset`] = Dataset.data;
            $scope[list.name] = $scope[`${list.iterator}_dataset`].results;
        }

        // iterate over the list and add fields like type label, after the
        // OPTIONS request returns, or the list is sorted/paginated/searched
        function optionsRequestDataProcessing(){
            $scope.optionsDefer.promise.then(function(options) {
                if($scope.list.name === 'instance_groups'){
                    if ($scope[list.name] !== undefined) {
                        $scope[list.name].forEach(function(item, item_idx) {
                            var itm = $scope[list.name][item_idx];
                            // Set the item type label
                            if (list.fields.kind && options && options.actions && options.actions.GET && options.actions.GET.kind) {
                                options.actions.GET.kind.choices.forEach(function(choice) {
                                    if (choice[0] === item.kind) {
                                        itm.kind_label = choice[1];
                                    }
                                });
                            }

                        });
                    }
                }
            });
        }

        $scope.$watchCollection(`${$scope.list.name}`, function() {
                optionsRequestDataProcessing();
            }
        );
    }
];