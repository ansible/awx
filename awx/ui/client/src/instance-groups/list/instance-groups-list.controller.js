export default ['$scope', 'resolvedModels', 'Dataset', '$state', 'ComponentsStrings', 'ProcessErrors', 'Wait',
    function($scope, resolvedModels, Dataset, $state, strings, ProcessErrors, Wait) {
        const vm = this;
        const { instanceGroup } = resolvedModels;

        vm.strings = strings;
        $scope.selection = {};

        init();

        function init(){
            $scope.list = {
                iterator: 'instance_group',
                name: 'instance_groups'
            };

            $scope.collection = {
                basePath: 'instance_groups',
                iterator: 'instance_group'
            };

            $scope[`${$scope.list.iterator}_dataset`] = Dataset.data;
            $scope[$scope.list.name] = $scope[`${$scope.list.iterator}_dataset`].results;
            $scope.instanceGroupCount = Dataset.data.count;

            $scope.$on('updateDataset', function(e, dataset) {
                $scope[`${$scope.list.iterator}_dataset`] = dataset;
                $scope[$scope.list.name] = dataset.results;
            });
        }

        $scope.$watch('$state.params.instance_group_id', () => {
            vm.activeId = parseInt($state.params.instance_group_id);
        });

        vm.delete = () => {
            Wait('start');
            let deletables = $scope.selection;
            deletables = Object.keys(deletables).filter((n) => deletables[n]);

            deletables.forEach((data) => {
                let promise = instanceGroup.http.delete({resource: data});
                Promise.resolve(promise).then(vm.onSaveSuccess)
                    .catch(({data, status}) => {
                        ProcessErrors($scope, data, status, null, {
                            hdr: 'Error!',
                            msg: 'Call failed. Return status: ' + status
                        });
                    })
                    .finally(() => {
                        Wait('stop');
                    });
            });
        };

        vm.onSaveSuccess = () => {
            $state.transitionTo($state.current, $state.params, {
                reload: true, location: true, inherit: false, notify: true
            });
        };

        $scope.createInstanceGroup = () => {
            $state.go('instanceGroups.add');
        };
    }
];
