export default function() {

    return {
        restrict: 'E',
        require: '^breadcrumbs',
        transclude: true,
        scope: {
            path: '@',
            title: '@',
            current: '@'
        },
        link: function(scope, element, attrs, parentController) {
            var breadcrumb =
                parentController.addBreadcrumb(scope.title, scope.path, scope.current);

            scope.$watch('title', function(value) {
                breadcrumb.title = value;

                if (breadcrumb.isCurrent && value) {
                    parentController.setHidden(false);
                }
            });
        }
    };

}
