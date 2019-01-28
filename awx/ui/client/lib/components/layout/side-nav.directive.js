const templateUrl = require('~components/layout/side-nav.partial.html');

let $document;

function atSideNavLink (scope, element, attrs, ctrl) {
    scope.layoutVm = ctrl;

    $document.on('click', (e) => {
        if ($(e.target).parents('.at-Layout-side').length === 0) {
            scope.$emit('clickOutsideSideNav');
        }
    });

    element.find('.at-SettingsSubPane').hover(() => {
        scope.vm.onSettingsSubPane = true;
    }, () => {
        scope.vm.onSettingsSubPane = false;
        setTimeout(() => {
            if (!scope.vm.onSettingsNavItem) {
                scope.vm.showSettingsSubMenu = false;
            }
        }, 100);
    });
}

function AtSideNavController ($scope, $window) {
    const vm = this || {};
    const breakpoint = 700;

    vm.isExpanded = true;

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

    $(window).resize(() => {
        if ($window.innerWidth <= breakpoint) {
            vm.isExpanded = false;
        } else {
            vm.isExpanded = true;
        }
    });
}

AtSideNavController.$inject = ['$scope', '$window'];

function atSideNav (_$document_) {
    $document = _$document_;

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

atSideNav.$inject = ['$document'];

export default atSideNav;
