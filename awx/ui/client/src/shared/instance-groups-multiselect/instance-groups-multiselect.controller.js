export default ['$scope',
    function($scope) {

        $scope.instanceGroupsTags = [];

        $scope.$watch('instanceGroups', function() {
            $scope.instanceGroupsTags = $scope.instanceGroups;
        }, true);

        $scope.deleteTag = function(tag){
            _.remove($scope.instanceGroups, {id: tag.id});
        };
    }
];