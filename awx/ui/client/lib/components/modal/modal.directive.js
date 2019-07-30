const templateUrl = require('~components/modal/modal.partial.html');

const DEFAULT_ANIMATION_DURATION = 150;

function atModalLink (scope, el, attrs, controllers) {
    const modalController = controllers[0];
    const property = `scope.${scope.ns}.modal`;

    const done = scope.$watch(property, () => {
        modalController.init(scope, el);
        done();
    });
}

function AtModalController (strings) {
    const vm = this;

    let overlay;

    vm.strings = strings;

    vm.init = (scope, el) => {
        overlay = el[0]; // eslint-disable-line prefer-destructuring

        vm.modal = scope[scope.ns].modal;
        vm.modal.show = vm.show;
        vm.modal.hide = vm.hide;
        vm.modal.onClose = scope.onClose;
    };

    vm.show = (title, message) => {
        vm.modal.title = title;
        vm.modal.message = message;

        overlay.style.display = 'block';
        overlay.style.opacity = 1;
    };

    vm.hide = () => {
        overlay.style.opacity = 0;

        setTimeout(() => {
            overlay.style.display = 'none';
        }, DEFAULT_ANIMATION_DURATION);

        if (vm.modal.onClose) {
            vm.modal.onClose();
        }
    };

    vm.clickToHide = event => {
        if ($(event.target).hasClass('at-Modal')) {
            vm.hide();
        }
    };
}

AtModalController.$inject = [
    'ComponentsStrings'
];

function atModal () {
    return {
        restrict: 'E',
        replace: true,
        transclude: true,
        require: ['atModal'],
        templateUrl,
        controller: AtModalController,
        controllerAs: 'vm',
        link: atModalLink,
        scope: true
    };
}

export default atModal;
