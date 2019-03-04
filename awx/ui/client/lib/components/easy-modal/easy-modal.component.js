const templateUrl = require('~components/easy-modal/easy-modal.partial.html');

const overlaySelector = '.at-EasyModal';

function EasyModalController ($element) {
    const vm = this || {};

    vm.$onInit = () => {
        const [el] = $element;
        const overlay = el.querySelector(overlaySelector);
        overlay.style.display = 'block';
        overlay.style.opacity = 1;
    };
}

EasyModalController.$inject = [
    '$element',
];

export default {
    templateUrl,
    controller: EasyModalController,
    controllerAs: 'vm',
    transclude: true,
    bindings: {
        title: '=',
        onClose: '=',
    },
};
