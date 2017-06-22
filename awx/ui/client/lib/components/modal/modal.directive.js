const DEFAULT_ANIMATION_DURATION = 150;

function atModalLink (scope, el, attrs, controllers) {
    let modalController = controllers[0];
    let property = `scope.${scope.ns}.modal`;

    let done = scope.$watch(property, () => {
        modalController.init(scope, el);
        done();
    });
}

function AtModalController (eventService) {
    let vm = this;

    let overlay;
    let modal;
    let listeners;

    vm.init = (scope, el) => {
        overlay = el[0];
        modal = el.find('.at-Modal-window')[0];

        vm.modal = scope[scope.ns].modal;
        vm.modal.show = vm.show;
        vm.modal.hide = vm.hide;
    };

    vm.show = (title, message) => {
        vm.modal.title = title;
        vm.modal.message = message;

        event.stopPropagation();

        listeners = eventService.addListeners([
            [window, 'click', vm.clickToHide]
        ]);

        overlay.style.display = 'block';
        overlay.style.opacity = 1;
    };

    vm.hide = () => {
        overlay.style.opacity = 0;

        eventService.remove(listeners);

        setTimeout(() => overlay.style.display = 'none', DEFAULT_ANIMATION_DURATION);
    };

    vm.clickToHide = event => {
        if (vm.clickIsOutsideModal(event)) {
            vm.hide();
        }
    };

    vm.clickIsOutsideModal = e => {
        let m = modal.getBoundingClientRect();
        let cx = e.clientX;
        let cy = e.clientY;
        
        if (cx < m.left || cx > m.right || cy > m.bottom || cy < m.top) {
            return true;
        }

        return false;
    };
}

AtModalController.$inject = ['EventService'];

function atModal (pathService) {
    return {
        restrict: 'E',
        replace: true,
        transclude: true,
        require: ['atModal'],
        templateUrl: pathService.getPartialPath('components/modal/modal'),
        controller: AtModalController,
        controllerAs: 'vm',
        link: atModalLink,
        scope: true
    };
}

atModal.$inject = [
    'PathService'
];

export default atModal;
