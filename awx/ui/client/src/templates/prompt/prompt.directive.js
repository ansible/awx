import promptController from './prompt.controller';
export default [ 'templateUrl',
    function(templateUrl) {
    return {
        scope: {
            promptData: '=',
            onFinish: '&',
            actionText: '@',
            preventCredsWithPasswords: '<',
            readOnlyPrompts: '='
        },
        templateUrl: templateUrl('templates/prompt/prompt'),
        replace: true,
        transclude: true,
        restrict: 'E',
        controller: promptController,
        controllerAs: 'vm',
        bindToController: true,
        link: function(scope, el, attrs, promptController) {
            scope.ns = 'launch';
            scope[scope.ns] = { modal: {} };

            promptController.init(scope);
        }
    };
}];
