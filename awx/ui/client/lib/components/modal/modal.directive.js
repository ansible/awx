const DEFAULT_ANIMATION_DURATION = 150;

function atModalLink (scope, el, attrs, controllers) {
    let modalController = controllers[0];
    let container = el[0];
    let property = `scope.${scope.ns}.modal`;

    let done = scope.$watch(property, () => {
        modalController.init(scope, container);
        done();
    });
}

function AtModalController (eventService) {
    let vm = this;

    let container;
    let listeners;

    vm.init = (scope, _container_) => {
        container = _container_;

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

        container.style.display = 'block';
        container.style.opacity = 1;
    };

    vm.hide = () => {
        container.style.opacity = 0;

        eventService.remove(listeners);

        setTimeout(() => {
            container.style.display = 'none';
            vm.modal.message = '';
            vm.modal.title = '';
        }, DEFAULT_ANIMATION_DURATION);
    };

    vm.clickToHide = event => {
        if (vm.clickIsOutsideContainer(event)) {
            console.log('outside');
        } else {
            console.log('inside');
        }
    };

    vm.clickIsOutsideContainer = e => {
        let pos = container.getBoundingClientRect();
        let ex = e.clientX;
        let ey = e.clientY;

        console.log(e, pos);
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
