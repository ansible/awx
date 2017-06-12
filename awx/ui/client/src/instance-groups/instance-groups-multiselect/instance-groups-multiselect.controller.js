export default ['$scope',
    function($scope) {

        $scope.instanceGroupsTags = [];

        $scope.$watch('instanceGroups', function() {
            $scope.instanceGroupsTags = _.map($scope.instanceGroups, (item) => item.name);
        }, true);
    }
];