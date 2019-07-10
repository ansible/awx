export default [function () {
    return {
        getMessagesObj: function ($scope, defaultMessages) {
            if (!$scope.customize_messages) {
              return null;
            }
            return {
                started: {
                    message: $scope.started_message === defaultMessages.started.message ?
                        null : $scope.started_message,
                    body: $scope.started_body === defaultMessages.started.body ?
                        null : $scope.started_body,
                },
                success: {
                    message: $scope.success_message === defaultMessages.success.message ?
                        null : $scope.success_message,
                    body: $scope.success_body === defaultMessages.success.body ?
                        null : $scope.success_body,
                },
                error: {
                    message: $scope.error_message === defaultMessages.error.message ?
                        null : $scope.error_message,
                    body: $scope.error_body === defaultMessages.error.body ?
                        null : $scope.error_body,
                }
            };
        },
        setMessagesOnScope: function ($scope, messages, defaultMessages) {
          $scope.started_message = defaultMessages.started.message;
          $scope.started_body = defaultMessages.started.body;
          $scope.success_message = defaultMessages.success.message;
          $scope.success_body = defaultMessages.success.body;
          $scope.error_message = defaultMessages.error.message;
          $scope.error_body = defaultMessages.error.body;
          if (!messages) {
            return;
          }
          let customized = false;
          if (messages.started.message) {
            customized = true;
            $scope.started_message = messages.started.message;
          }
          if (messages.started.body) {
            customized = true;
            $scope.started_body = messages.started.body;
          }
          if (messages.success.message) {
            customized = true;
            $scope.success_message = messages.success.message;
          }
          if (messages.success.body) {
            customized = true;
            $scope.success_body = messages.success.body;
          }
          if (messages.error.message) {
            customized = true;
            $scope.error_message = messages.error.message;
          }
          if (messages.error.body) {
            customized = true;
            $scope.error_body = messages.error.body;
          }
          $scope.customize_messages = customized;
        }
    };
}];
