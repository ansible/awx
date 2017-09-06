function atTopNavItemLink (scope, element, attrs, ctrl) {
    scope.layoutVm = ctrl;

    scope.isHidden = false;

    var shownWhen = attrs.isShown;

    if (shownWhen !== 'missingLicense') {
        scope.$watch('layoutVm.licenseIsMissing', function(val) {
            scope.isHidden = val;
        });
    }
}

function atTopNavItem (pathService) {
    return {
        restrict: 'E',
        replace: true,
        transclude: true,
        templateUrl: pathService.getPartialPath('components/layout/top-nav-item'),
        require: '^^atLayout',
        link: atTopNavItemLink,
        scope: {
        }
    };
}

atTopNavItem.$inject = ['PathService'];

export default atTopNavItem;
