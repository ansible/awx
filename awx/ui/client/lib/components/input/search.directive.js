const DEFAULT_PLACEHOLDER = 'SEARCH';

function atInputSearchLink (scope, element, attrs, controllers) {
    let inputController = controllers[0];
    let property = `scope.${scope.ns}.search`;

    let done = scope.$watch(property, () => {
        inputController.init(scope, element);
        done();
    });
}

function AtInputSearchController (baseInputController) {
    let vm = this || {};

    let toggleButton;
    let input;

    vm.init = (scope, element) => {
        toggleButton = element.find('.at-InputSearch-toggle')[0];
        input = element.find('.at-Input')[0];

        vm.placeholder = DEFAULT_PLACEHOLDER;
        vm.search = scope[scope.ns].search;
        // baseInputController.call(vm, 'input', scope, element, form);

        //vm.check();
    };

    vm.toggle = () => {
        input.focus();
        vm.isToggleActive = !vm.isToggleActive;
    };
}

AtInputSearchController.$inject = ['BaseInputController'];

function atInputSearch (pathService) {
    return {
        restrict: 'E',
        transclude: true,
        replace: true,
        require: ['atInputSearch'],
        templateUrl: pathService.getPartialPath('components/input/search'),
        controller: AtInputSearchController,
        controllerAs: 'vm',
        link: atInputSearchLink,
        scope: true
    };
}

atInputSearch.$inject = ['PathService'];

export default atInputSearch;
