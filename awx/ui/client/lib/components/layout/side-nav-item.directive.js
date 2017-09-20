const templateUrl = require('~components/layout/side-nav-item.partial.html');

function atSideNavItemLink (scope, element, attrs, ctrl) {
    [scope.navVm, scope.layoutVm] = ctrl;
}

function AtSideNavItemController ($state, $scope, strings) {
    const vm = this || {};

    $scope.$watch('layoutVm.currentState', current => {
        if ($scope.name === 'portal mode') {
            vm.isRoute = (current && current.indexOf('portalMode') === 0);
        } else if (current && current.indexOf($scope.route) === 0) {
            if (current.indexOf('jobs.schedules') === 0 && $scope.route === 'jobs') {
                vm.isRoute = false;
            } else {
                vm.isRoute = true;
            }
        } else {
            vm.isRoute = false;
        }
    });

    vm.go = () => {
        $state.go($scope.route, {}, { reload: true });
    };

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

AtSideNavItemController.$inject = ['$state', '$scope', 'ComponentsStrings'];

function atSideNavItem () {
    return {
        restrict: 'E',
        templateUrl,
        require: ['^^atSideNav', '^^atLayout'],
        controller: AtSideNavItemController,
        controllerAs: 'vm',
        link: atSideNavItemLink,
        scope: {
            iconClass: '@',
            name: '@',
            route: '@',
            systemAdminOnly: '@'
        }
    };
}

export default atSideNavItem;
