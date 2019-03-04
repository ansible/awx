const templateUrl = require('~components/action/action-button.partial.html');

function ActionButtonController () {
    const vm = this || {};
    vm.$onInit = () => {
        const { variant } = vm;

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

export default {
    templateUrl,
    controller: ActionButtonController,
    controllerAs: 'vm',
    transclude: true,
    bindings: {
        variant: '@',
    },
};
