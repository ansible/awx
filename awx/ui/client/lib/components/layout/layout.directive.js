import defaultStrings from '~assets/default.strings.json';

const templateUrl = require('~components/layout/layout.partial.html');

function AtLayoutController ($scope, $http, strings, ProcessErrors, $transitions) {
    const vm = this || {};

    vm.product = defaultStrings.BRAND_NAME;

    $transitions.onSuccess({}, (transition) => {
        vm.currentState = transition.to().name;
    });

    $scope.$watch('$root.current_user', (val) => {
        vm.isLoggedIn = val && val.username;
        if (!_.isEmpty(val)) {
            vm.isSuperUser = $scope.$root.user_is_superuser || $scope.$root.user_is_system_auditor;
            vm.currentUsername = val.username;
            vm.currentUserId = val.id;

            if (!vm.isSuperUser) {
                checkOrgAdmin();
                checkNotificationAdmin();
            }
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

    function checkOrgAdmin () {
        const usersPath = `/api/v2/users/${vm.currentUserId}/admin_of_organizations/`;
        $http.get(usersPath)
            .then(({ data }) => {
                if (data.count > 0) {
                    vm.isOrgAdmin = true;
                } else {
                    vm.isOrgAdmin = false;
                }
            })
            .catch(({ data, status }) => {
                ProcessErrors(null, data, status, null, {
                    hdr: strings.get('error.HEADER'),
                    msg: strings.get('error.CALL', { path: usersPath, action: 'GET', status })
                });
            });
    }

    function checkNotificationAdmin () {
        const usersPath = `/api/v2/users/${vm.currentUserId}/roles/?role_field=notification_admin_role`;
        $http.get(usersPath)
            .then(({ data }) => {
                if (data.count > 0) {
                    vm.isNotificationAdmin = true;
                } else {
                    vm.isNotificationAdmin = false;
                }
            })
            .catch(({ data, status }) => {
                ProcessErrors(null, data, status, null, {
                    hdr: strings.get('error.HEADER'),
                    msg: strings.get('error.CALL', { path: usersPath, action: 'GET', status })
                });
            });
    }
}

AtLayoutController.$inject = ['$scope', '$http', 'ComponentsStrings', 'ProcessErrors', '$transitions'];

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
