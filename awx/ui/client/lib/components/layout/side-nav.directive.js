function atSideNavLink (scope, element, attrs, ctrl) {
    scope.layoutVm = ctrl;
}

function AtSideNavController () {
    let vm = this || {};

    vm.isExpanded = true;

    vm.toggleExpansion = () => {
        vm.isExpanded = !vm.isExpanded;
    }
}

function atSideNav (pathService) {
    return {
        restrict: 'E',
        replace: true,
        require: '^^atLayout',
        controller: AtSideNavController,
        controllerAs: 'vm',
        link: atSideNavLink,
        transclude: true,
        templateUrl: pathService.getPartialPath('components/layout/side-nav'),
        scope: {
        }
    };
}

atSideNav.$inject = ['PathService'];

export default atSideNav;
