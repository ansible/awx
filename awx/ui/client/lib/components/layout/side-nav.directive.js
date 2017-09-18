const templateUrl = require('@components/layout/side-nav.partial.html');

function atSideNavLink (scope, element, attrs, ctrl) {
    scope.layoutVm = ctrl;
}

function AtSideNavController () {
    let vm = this || {};

    vm.isExpanded = false;

    vm.toggleExpansion = () => {
        vm.isExpanded = !vm.isExpanded;
    }
}

function atSideNav () {
    return {
        restrict: 'E',
        replace: true,
        require: '^^atLayout',
        controller: AtSideNavController,
        controllerAs: 'vm',
        link: atSideNavLink,
        transclude: true,
        templateUrl,
        scope: {
        }
    };
}

export default atSideNav;
