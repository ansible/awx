export default ['$scope', 'InstanceGroupList', 'GetBasePath', 'Rest', 'Dataset','Find', '$state',
    function($scope, InstanceGroupList, GetBasePath, Rest, Dataset, Find, $state) {
        let list = InstanceGroupList;

        init();

        function init(){
            $scope.list = list;
            $scope[`${list.iterator}_dataset`] = Dataset.data;
            $scope[list.name] = $scope[`${list.iterator}_dataset`].results;
            $scope.instanceGroupCount = Dataset.data.count;
        }

        $scope.isActive = function(id) {
            let selected = parseInt($state.params.instance_group_id);
            return id === selected;
        };
    }
];