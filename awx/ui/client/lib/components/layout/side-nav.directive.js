const templateUrl = require('~components/layout/side-nav.partial.html');

function atSideNavLink (scope, element, attrs, ctrl) {
    scope.layoutVm = ctrl;

    document.on('click', (e) => {
        if ($(e.target).parents('.at-Layout-side').length === 0) {
            scope.$emit('clickOutsideSideNav');
        }
    });
}

function AtSideNavController ($scope, $window) {
    let vm = this || {};
    const breakpoint = 700;

    vm.isExpanded = false;

    vm.toggleExpansion = () => {
        vm.isExpanded = !vm.isExpanded;
    };

    $scope.$watch('layoutVm.currentState', () => {
        if ($window.innerWidth <= breakpoint) {
            vm.isExpanded = false;
        }
    });

    $scope.$on('clickOutsideSideNav', () => {
        if ($window.innerWidth <= breakpoint) {
            vm.isExpanded = false;
        }
    });
}

AtSideNavController.$inject = ['$scope', '$window'];

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
