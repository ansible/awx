
const emptyDefaults = {
    started: {
        message: '',
        body: '',
    },
    success: {
        message: '',
        body: '',
    },
    error: {
        message: '',
        body: '',
    },
};

export default [function() {
    return {
        getMessagesObj: function ($scope, defaultMessages) {
            if (!$scope.customize_messages) {
              return null;
            }
            const defaults = defaultMessages[$scope.notification_type.value] || {};
            return {
                started: {
                    message: $scope.started_message === defaults.started.message ?
                        null : $scope.started_message,
                    body: $scope.started_body === defaults.started.body ?
                        null : $scope.started_body,
                },
                success: {
                    message: $scope.success_message === defaults.success.message ?
                        null : $scope.success_message,
                    body: $scope.success_body === defaults.success.body ?
                        null : $scope.success_body,
                },
                error: {
                    message: $scope.error_message === defaults.error.message ?
                        null : $scope.error_message,
                    body: $scope.error_body === defaults.error.body ?
                        null : $scope.error_body,
                }
            };
        },

        setMessagesOnScope: function ($scope, messages, defaultMessages) {
            let defaults;
            if ($scope.notification_type) {
                defaults = defaultMessages[$scope.notification_type.value] || emptyDefaults;
            } else {
                defaults = emptyDefaults;
            }
            $scope.started_message = defaults.started.message;
            $scope.started_body = defaults.started.body;
            $scope.success_message = defaults.success.message;
            $scope.success_body = defaults.success.body;
            $scope.error_message = defaults.error.message;
            $scope.error_body = defaults.error.body;
            if (!messages) {
                return;
            }
            let isCustomized = false;
            if (messages.started.message) {
                isCustomized = true;
                $scope.started_message = messages.started.message;
            }
            if (messages.started.body) {
                isCustomized = true;
                $scope.started_body = messages.started.body;
            }
            if (messages.success.message) {
                isCustomized = true;
                $scope.success_message = messages.success.message;
            }
            if (messages.success.body) {
                isCustomized = true;
                $scope.success_body = messages.success.body;
            }
            if (messages.error.message) {
                isCustomized = true;
                $scope.error_message = messages.error.message;
            }
            if (messages.error.body) {
                isCustomized = true;
                $scope.error_body = messages.error.body;
            }
            $scope.customize_messages = isCustomized;
        },

        updateDefaultsOnScope: function(
            $scope,
            oldDefaults = emptyDefaults,
            newDefaults = emptyDefaults
        ) {
            if ($scope.started_message === oldDefaults.started.message) {
                $scope.started_message = newDefaults.started.message;
            }
            if ($scope.started_body === oldDefaults.started.body) {
                $scope.started_body = newDefaults.started.body;
            }
            if ($scope.success_message === oldDefaults.success.message) {
                $scope.success_message = newDefaults.success.message;
            }
            if ($scope.success_body === oldDefaults.success.body) {
                $scope.success_body = newDefaults.success.body;
            }
            if ($scope.error_message === oldDefaults.error.message) {
                $scope.error_message = newDefaults.error.message;
            }
            if ($scope.error_body === oldDefaults.error.body) {
                $scope.error_body = newDefaults.error.body;
            }
        }
    };
}];
