export default ['$scope', 'InstanceList', 'GetBasePath', 'Rest', 'Dataset','Find', '$state', '$q',
    function($scope, InstanceList, GetBasePath, Rest, Dataset, Find, $state, $q) {
        let list = InstanceList;

        init();

        function init(){
            $scope.optionsDefer = $q.defer();
            $scope.list = list;
            $scope[`${list.iterator}_dataset`] = Dataset.data;
            $scope[list.name] = $scope[`${list.iterator}_dataset`].results;
        }

        $scope.isActive = function(id) {
            let selected = parseInt($state.params.instance_id);
            return id === selected;
        };

    }
];