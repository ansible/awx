const DEFAULT_PLACEHOLDER = 'SEARCH';

function atSearchLink (scope, element, attrs, controllers) {
    let inputController = controllers[0];
    let property = `scope.${scope.ns}.search`;

    let done = scope.$watch(property, () => {
        inputController.init(scope, element);
        scope.ready = true;
        done();
    });
}

function AtSearchController () {
    let vm = this || {};

    let toggleButton;
    let input;

    vm.init = (scope, element) => {
        toggleButton = element.find('.at-Search-toggle')[0];
        input = element.find('.at-Input')[0];

        vm.placeholder = DEFAULT_PLACEHOLDER;
        vm.search = scope[scope.ns].search;
    };

    vm.toggle = () => {
        input.focus();
        vm.isToggleActive = !vm.isToggleActive;
    };
}

function atSearch (pathService) {
    return {
        restrict: 'E',
        transclude: true,
        replace: true,
        require: ['atSearch'],
        templateUrl: pathService.getPartialPath('components/search/search'),
        controller: AtSearchController,
        controllerAs: 'vm',
        link: atSearchLink,
        scope: true
    };
}

atSearch.$inject = ['PathService'];

export default atSearch;
