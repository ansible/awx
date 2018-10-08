const templateUrl = require('~components/layout/side-nav-item.partial.html');

function atSideNavItemLink (scope, element, attrs, ctrl) {
    [scope.navVm, scope.layoutVm] = ctrl;

    if (attrs.showSettingsSubMenu) {
        element.hover(() => {
            scope.navVm.onSettingsNavItem = true;
            scope.navVm.showSettingsSubMenu = true;
        }, () => {
            scope.navVm.onSettingsNavItem = false;
            setTimeout(() => {
                if (!scope.navVm.onSettingsSubPane) {
                    scope.navVm.showSettingsSubMenu = false;
                }
            }, 100);
        });
    }
}

function AtSideNavItemController ($scope, strings) {
    const vm = this || {};

    $scope.$watch('layoutVm.currentState', current => {
        if ($scope.name === 'portal mode') {
            vm.isRoute = (current && current.indexOf('portalMode') === 0);
        } else if (current && current.indexOf($scope.route) === 0) {
            if (current.indexOf('schedules') === 0 && $scope.route === 'jobs') {
                vm.isRoute = false;
            } else {
                vm.isRoute = true;
            }
        } else {
            vm.isRoute = false;
        }
    });

    vm.tooltip = {
        popover: {
            text: strings.get(`layout.${$scope.name}`),
            on: 'mouseenter',
            icon: $scope.iconClass,
            position: 'right',
            arrowHeight: 18
        }
    };
}

AtSideNavItemController.$inject = ['$scope', 'ComponentsStrings'];

function atSideNavItem () {
    return {
        restrict: 'E',
        templateUrl,
        require: ['^^atSideNav', '^^atLayout'],
        controller: AtSideNavItemController,
        controllerAs: 'vm',
        link: atSideNavItemLink,
        transclude: true,
        scope: {
            iconClass: '@',
            name: '@',
            route: '@',
            systemAdminOnly: '@',
            noTooltipOnCollapsed: '@'
        }
    };
}

export default atSideNavItem;
