function atSearchKeyLink (scope, element, attrs, controllers) {
    let searchController = controllers[0];
    let property = `scope.${scope.ns}.search`;

    let done = scope.$watch(property, () => {
        searchController.init(scope, element);
        done();
    });
}

function AtSearchKeyController () {
    let vm = this || {};

    vm.init = (scope, element) => {
        /*
         *vm.placeholder = DEFAULT_PLACEHOLDER;
         *vm.search = scope[scope.ns].search;
         */
    };
}

function atSearchKey (pathService) {
    return {
        restrict: 'E',
        transclude: true,
        replace: true,
        require: ['atSearchKey'],
        templateUrl: pathService.getPartialPath('components/search/key'),
        controller: AtSearchKeyController,
        controllerAs: 'vm',
        link: atSearchKeyLink,
        scope: true
    };
}

atSearchKey.$inject = ['PathService'];

export default atSearchKey;
