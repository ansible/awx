const templateUrl = require('~components/dialog/dialog.partial.html');

const overlaySelector = '.at-Dialog';

function DialogController ($element) {
    const vm = this || {};

    vm.$onInit = () => {
        const [el] = $element;
        const overlay = el.querySelector(overlaySelector);
        overlay.style.display = 'block';
        overlay.style.opacity = 1;
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
