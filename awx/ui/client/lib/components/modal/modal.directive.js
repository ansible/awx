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

function AtModalController (eventService, strings) {
    const vm = this;

    let overlay;
    let modal;
    let listeners;

    vm.strings = strings;

    vm.init = (scope, el) => {
        [overlay] = el;
        [modal] = el.find('.at-Modal-window');

        vm.modal = scope[scope.ns].modal;
        vm.modal.show = vm.show;
        vm.modal.hide = vm.hide;
    };

    vm.show = (title, message) => {
        vm.modal.title = title;
        vm.modal.message = message;

        listeners = eventService.addListeners([
            [window, 'click', vm.clickToHide]
        ]);

        overlay.style.display = 'block';
        overlay.style.opacity = 1;
    };

    vm.hide = () => {
        overlay.style.opacity = 0;

        eventService.remove(listeners);

        setTimeout(() => {
            overlay.style.display = 'none';
        }, DEFAULT_ANIMATION_DURATION);
    };

    vm.clickToHide = event => {
        if (vm.clickIsOutsideModal(event)) {
            vm.hide();
        }
    };

    vm.clickIsOutsideModal = e => {
        const m = modal.getBoundingClientRect();
        const cx = e.clientX;
        const cy = e.clientY;

        if (cx < m.left || cx > m.right || cy > m.bottom || cy < m.top) {
            return true;
        }

        return false;
    };
}

AtModalController.$inject = [
    'EventService',
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
