const DEFAULT_ANIMATION_DURATION = 150;

function atModalLink (scope, el, attr, controllers) {
    let modalController = controllers[0];
    let container = el[0];

    modalController.init(scope, container);
}

function AtModalController () {
    let vm = this;

    let scope;
    let container;

    vm.init = (_scope_, _container_) => {
        scope = _scope_;
        container = _container_;

        scope.state.show = vm.show;
        scope.state.hide = vm.hide;
    };

    vm.show = (title, message) => {
        scope.title = title;
        scope.message = message;

        container.style.display = 'block';
        container.style.opacity = 1;
    };

    vm.hide = () => {
        container.style.opacity = 0;

        setTimeout(() => {
            container.style.display = 'none';
            scope.message = '';
            scope.title = '';
        }, DEFAULT_ANIMATION_DURATION);
    };
}

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
        scope: {
            state: '='
        }
    };
}

atModal.$inject = [
    'PathService'
];

export default atModal;
