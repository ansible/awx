export default ['$scope', 'InstanceGroupList', 'resolvedModels', 'GetBasePath', 'Rest', 'Dataset','Find', '$state', '$q', 'ComponentsStrings',
    function($scope, InstanceGroupList, resolvedModels, GetBasePath, Rest, Dataset, Find, $state, $q, strings) {
        let list = InstanceGroupList;
        const vm = this;
        const { instanceGroup } = resolvedModels;

        init();

        function init(){
            vm.panelTitle = strings.get('layout.INSTANCE_GROUPS');
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
            //refactor
            deletables.forEach((data) => {
                let promise = instanceGroup.http.delete({resource: data})
                Promise.resolve(promise).then(vm.onSaveSuccess);
            });
        }

        vm.onSaveSuccess = () => {
            $state.transitionTo($state.current, $state.params, {
                reload: true, location: true, inherit: false, notify: true
            });
        }

        $scope.createInstanceGroup = () => {
            $state.go('instanceGroups.add');
        };
    }
];
