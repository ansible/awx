const templateUrl = require('~components/action/action-button.partial.html');

function link (scope, element, attrs, controllers) {
    const [actionButtonController] = controllers;

    actionButtonController.init(scope);
}

function ActionButtonController () {
    const vm = this || {};

    vm.init = (scope) => {
        const { variant } = scope;

        if (variant === 'primary') {
            vm.color = 'success';
            vm.fill = '';
        }

        if (variant === 'secondary') {
            vm.color = 'info';
            vm.fill = '';
        }

        if (variant === 'tertiary') {
            vm.color = 'default';
            vm.fill = 'Hollow';
        }
    };
}

function atActionButton () {
    return {
        restrict: 'E',
        transclude: true,
        replace: true,
        templateUrl,
        require: ['atActionButton'],
        controller: ActionButtonController,
        controllerAs: 'vm',
        link,
        scope: {
            variant: '@',
        }
    };
}

export default atActionButton;
