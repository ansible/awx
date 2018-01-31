export default ['$scope', 'InstanceGroupList', 'resolvedModels', 'Dataset', '$state', 'ComponentsStrings', 'ProcessErrors',
    function($scope, InstanceGroupList, resolvedModels, Dataset, $state, strings, ProcessErrors) {
        let list = InstanceGroupList;
        const vm = this;
        const { instanceGroup } = resolvedModels;

        vm.strings = strings;

        init();

        function init(){
            $scope.list = list;
            $scope[`${list.iterator}_dataset`] = Dataset.data;
            $scope[list.name] = $scope[`${list.iterator}_dataset`].results;
            $scope.instanceGroupCount = Dataset.data.count;
        }

        $scope.selection = {};

        $scope.$watch('$state.params.instance_group_id', () => {
            vm.activeId = parseInt($state.params.instance_group_id);
        });

        vm.delete = () => {
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
