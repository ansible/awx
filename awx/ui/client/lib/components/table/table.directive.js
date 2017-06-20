function atTableLink (scope, element, attrs, controllers) {
    let tableController = controllers[0];

    tableController.init(scope, element);
}

function AtTableController (baseInputController) {
    let vm = this || {};

    vm.init = (scope, element) => {

    };
}

AtTableController.$inject = ['BaseInputController'];

function atTable (pathService) {
    return {
        restrict: 'E',
        transclude: true,
        replace: true,
        require: ['atTable'],
        templateUrl: pathService.getPartialPath('components/table/table'),
        controller: AtTableController,
        controllerAs: 'vm',
        link: atTableLink,
        scope: {
            state: '=',
            col: '@'
        }
    };
}

atTable.$inject = ['PathService'];

export default atTable;
