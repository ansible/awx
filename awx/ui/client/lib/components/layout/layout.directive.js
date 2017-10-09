const templateUrl = require('~components/layout/layout.partial.html');

function AtLayoutController ($scope, strings, $transitions) {
    const vm = this || {};

    $transitions.onSuccess({}, (transition) => {
        vm.currentState = transition.to().name;
    });

    $scope.$watch('$root.current_user', (val) => {
        vm.isLoggedIn = val && val.username;
        if (val) {
            vm.isSuperUser = $scope.$root.user_is_superuser || $scope.$root.user_is_system_auditor;
            vm.currentUsername = val.username;
            vm.currentUserId = val.id;
        }
    });

    $scope.$watch('$root.socketStatus', (newStatus) => {
        vm.socketState = newStatus;
        vm.socketIconClass = `icon-socket-${vm.socketState}`;
    });

    $scope.$watch('$root.licenseMissing', (licenseMissing) => {
        vm.licenseIsMissing = licenseMissing;
    });

    vm.getString = string => {
        try {
            return strings.get(`layout.${string}`);
        } catch (err) {
            return strings.get(string);
        }
    };
}

AtLayoutController.$inject = ['$scope', 'ComponentsStrings', '$transitions'];

function atLayout () {
    return {
        restrict: 'E',
        replace: true,
        transclude: true,
        templateUrl,
        controller: AtLayoutController,
        controllerAs: 'vm',
        scope: {}
    };
}

export default atLayout;
