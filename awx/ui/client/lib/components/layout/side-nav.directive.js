const templateUrl = require('~components/layout/side-nav.partial.html');

function atSideNavLink (scope, element, attrs, ctrl) {
    scope.layoutVm = ctrl;
}

function AtSideNavController ($scope) {
    let vm = this || {};

    vm.isExpanded = false;

    vm.toggleExpansion = () => {
        vm.isExpanded = !vm.isExpanded;
    }

    document.body.onclick = (e) => {
        if ($(e.target).parents(".at-Layout-side").length === 0) {
            vm.isExpanded = false;
        }
    }

    $scope.$on('$locationChangeStart', function(event) {
        vm.isExpanded = false;
    });
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
