export default [function () {
    return {
        getMessagesObj: function ($scope, defaultMessages) {
            if (!$scope.customize_messages) {
              return null;
            }
            return {
                start: {
                    message: $scope.start_message === defaultMessages.start_message
                        ? null : $scope.start_message,
                    body: $scope.start_body === defaultMessages.start_body
                        ? null : $scope.start_body,
                },
                success: {
                    message: $scope.success_message === defaultMessages.success_message
                        ? null : $scope.success_message,
                    body: $scope.success_body === defaultMessages.success_body
                        ? null : $scope.success_body,
                },
                error: {
                    message: $scope.error_message === defaultMessages.error_message
                        ? null : $scope.error_message,
                    body: $scope.error_body === defaultMessages.error_body
                        ? null : $scope.error_body,
                }
            };
        },
        setMessagesOnScope: function ($scope, messages, defaultMessages) {
          $scope.start_message = defaultMessages.start_message;
          $scope.success_message = defaultMessages.success_message;
          $scope.error_message = defaultMessages.error_message;
          if (!messages) {
            return;
          }
          let customized = false;
          if (messages.start.message) {
            customized = true;
            $scope.start_message = messages.start.message;
          }
          if (messages.start.body) {
            customized = true;
            $scope.start_body = messages.start.body;
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
    }
}]
