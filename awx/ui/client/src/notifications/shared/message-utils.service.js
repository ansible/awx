
const emptyDefaults = {
    started: { message: '', body: '' },
    success: { message: '', body: '' },
    error: { message: '', body: '' },
    workflow_approval: {
      approved: { message: '', body: '' },
      denied: { message: '', body: '' },
      running: { message: '', body: '' },
      timed_out: { message: '', body: '' },
    }
};

function getMessageIfUpdated(message, defaultValue) {
  return message === defaultValue ? null : message;
}

export default [function() {
    return {
        getMessagesObj: function ($scope, defaultMessages) {
            if (!$scope.customize_messages) {
              return null;
            }
            const defaults = defaultMessages[$scope.notification_type.value] || {};
            return {
                started: {
                    message: getMessageIfUpdated($scope.started_message, defaults.started.message),
                    body: getMessageIfUpdated($scope.started_body, defaults.started.body),
                },
                success: {
                    message: getMessageIfUpdated($scope.success_message, defaults.success.message),
                    body: getMessageIfUpdated($scope.success_body, defaults.success.body),
                },
                error: {
                    message: getMessageIfUpdated($scope.error_message, defaults.error.message),
                    body: getMessageIfUpdated($scope.error_body, defaults.error.body),
                },
                workflow_approval: {
                  approved: {
                    message: getMessageIfUpdated($scope.approved_message, defaults.workflow_approval.approved.message),
                    body: getMessageIfUpdated($scope.approved_body, defaults.workflow_approval.approved.body),
                  },
                  denied: {
                    message: getMessageIfUpdated($scope.denied_message, defaults.workflow_approval.denied.message),
                    body: getMessageIfUpdated($scope.denied_body, defaults.workflow_approval.denied.body),
                  },
                  running: {
                    message: getMessageIfUpdated($scope.running_message, defaults.workflow_approval.running.message),
                    body: getMessageIfUpdated($scope.running_body, defaults.workflow_approval.running.body),
                  },
                  timed_out: {
                    message: getMessageIfUpdated($scope.timed_out_message, defaults.workflow_approval.timed_out.message),
                    body: getMessageIfUpdated($scope.timed_out_body, defaults.workflow_approval.timed_out.body),
                  },
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
            $scope.approved_message = defaults.workflow_approval.approved.message;
            $scope.approved_body = defaults.workflow_approval.approved.body;
            $scope.denied_message = defaults.workflow_approval.denied.message;
            $scope.denied_body = defaults.workflow_approval.denied.body;
            $scope.running_message = defaults.workflow_approval.running.message;
            $scope.running_body = defaults.workflow_approval.running.body;
            $scope.timed_out_message = defaults.workflow_approval.timed_out.message;
            $scope.timed_out_body = defaults.workflow_approval.timed_out.body;

            if (!messages) {
                return;
            }
            let isCustomized = false;
            if (messages.started && messages.started.message) {
                isCustomized = true;
                $scope.started_message = messages.started.message;
            }
            if (messages.started && messages.started.body) {
                isCustomized = true;
                $scope.started_body = messages.started.body;
            }
            if (messages.success && messages.success.message) {
                isCustomized = true;
                $scope.success_message = messages.success.message;
            }
            if (messages.success && messages.success.body) {
                isCustomized = true;
                $scope.success_body = messages.success.body;
            }
            if (messages.error && messages.error.message) {
                isCustomized = true;
                $scope.error_message = messages.error.message;
            }
            if (messages.error && messages.error.body) {
                isCustomized = true;
                $scope.error_body = messages.error.body;
            }
            if (messages.workflow_approval) {
                if (messages.workflow_approval.approved &&
                    messages.workflow_approval.approved.message) {
                    isCustomized = true;
                    $scope.approved_message = messages.workflow_approval.approved.message;
                }
                if (messages.workflow_approval.approved &&
                    messages.workflow_approval.approved.body) {
                    isCustomized = true;
                    $scope.approved_body = messages.workflow_approval.approved.body;
                }
                if (messages.workflow_approval.denied &&
                    messages.workflow_approval.denied.message) {
                    isCustomized = true;
                    $scope.denied_message = messages.workflow_approval.denied.message;
                }
                if (messages.workflow_approval.denied &&
                    messages.workflow_approval.denied.body) {
                    isCustomized = true;
                    $scope.denied_body = messages.workflow_approval.denied.body;
                }
                if (messages.workflow_approval.running &&
                    messages.workflow_approval.running.message) {
                    isCustomized = true;
                    $scope.running_message = messages.workflow_approval.running.message;
                }
                if (messages.workflow_approval.running &&
                    messages.workflow_approval.running.body) {
                    isCustomized = true;
                    $scope.running_body = messages.workflow_approval.running.body;
                }
                if (messages.workflow_approval.timed_out &&
                    messages.workflow_approval.timed_out.message) {
                    isCustomized = true;
                    $scope.timed_out_message = messages.workflow_approval.timed_out.message;
                }
                if (messages.workflow_approval.timed_out &&
                    messages.workflow_approval.timed_out.body) {
                    isCustomized = true;
                    $scope.timed_out_body = messages.workflow_approval.timed_out.body;
                }
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
            if ($scope.approved_message === oldDefaults.workflow_approval.approved.message) {
                $scope.approved_message = newDefaults.workflow_approval.approved.message;
            }
            if ($scope.approved_body === oldDefaults.workflow_approval.approved.body) {
                $scope.approved_body = newDefaults.workflow_approval.approved.body;
            }
            if ($scope.denied_message === oldDefaults.workflow_approval.denied.message) {
                $scope.denied_message = newDefaults.workflow_approval.denied.message;
            }
            if ($scope.denied_body === oldDefaults.workflow_approval.denied.body) {
                $scope.denied_body = newDefaults.workflow_approval.denied.body;
            }
            if ($scope.running_message === oldDefaults.workflow_approval.running.message) {
                $scope.running_message = newDefaults.workflow_approval.running.message;
            }
            if ($scope.running_body === oldDefaults.workflow_approval.running.body) {
                $scope.running_body = newDefaults.workflow_approval.running.body;
            }
            if ($scope.timed_out_message === oldDefaults.workflow_approval.timed_out.message) {
                $scope.timed_out_message = newDefaults.workflow_approval.timed_out.message;
            }
            if ($scope.timed_out_body === oldDefaults.workflow_approval.timed_out.body) {
                $scope.timed_out_body = newDefaults.workflow_approval.timed_out.body;
            }
        }
    };
}];
