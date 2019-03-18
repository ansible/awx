const templateUrl = require('~components/dialog/dialog.partial.html');

const overlayClass = 'at-Dialog';

function DialogController () {
    const vm = this || {};

    vm.handleClick = ({ target }) => {
        if (!vm.onClose) {
            return;
        }

        const targetElement = $(target);

        if (targetElement.hasClass(overlayClass)) {
            vm.onClose();
        }
    };
}

DialogController.$inject = [
    '$element',
];

export default {
    templateUrl,
    controller: DialogController,
    controllerAs: 'vm',
    transclude: true,
    bindings: {
        title: '=',
        onClose: '=',
    },
};
