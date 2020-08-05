export default ['$scope',
    function($scope) {

        $scope.galaxyCredentialsTags = [];

        $scope.$watch('galaxyCredentials', function() {
            $scope.galaxyCredentialsTags = $scope.galaxyCredentials;
        }, true);

        $scope.deleteTag = function(tag){
            _.remove($scope.galaxyCredentials, {id: tag.id});
        };
    }
];