export default
    [   '$scope',
        '$rootScope',
        function($scope, $rootScope) {

    $scope.breadcrumbs = [];

    this.addBreadcrumb = function(title, path) {
        var breadcrumb =
            {   title: title,
                path: path
            };

        if ($rootScope.enteredPath === path) {
            breadcrumb.isCurrent = true;
        }

        $scope.breadcrumbs =
            $scope.breadcrumbs.concat(breadcrumb);

        return breadcrumb;
    };

    this.setHidden = function(hidden) {

        if (angular.isUndefined(hidden)) {
            $scope.isHidden = true;
        } else {
            $scope.isHidden = hidden;
        }

    };

}];
