const templateUrl = require('~components/layout/top-nav-item.partial.html');

function atTopNavItemLink (scope, element, attrs, ctrl) {
    scope.layoutVm = ctrl;

    scope.isHidden = false;

    const shownWhen = attrs.isShown;

    if (shownWhen !== 'missingLicense') {
        scope.$watch('layoutVm.licenseIsMissing', (val) => {
            scope.isHidden = val;
        });
    }
}

function atTopNavItem () {
    return {
        restrict: 'E',
        replace: true,
        transclude: true,
        templateUrl,
        require: '^^atLayout',
        link: atTopNavItemLink,
        scope: {
        }
    };
}

export default atTopNavItem;
