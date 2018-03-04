const templateUrl = require('~features/output/search-key.partial.html');

function atSearchKeyLink (scope, el, attrs, controllers) {
    const [atSearchKeyController] = controllers;

    atSearchKeyController.init(scope);
}

function AtSearchKeyController () {
    const vm = this || {};

    vm.init = scope => {
        vm.examples = scope.examples || [];
        vm.fields = scope.fields || [];
        vm.relatedFields = scope.relatedFields || [];
    }
}

AtSearchKeyController.$inject = ['$scope'];


function atSearchKey () {
    return {
        templateUrl,
        restrict: 'E',
        require: ['atSearchKey'],
        controllerAs: 'vm',
        link: atSearchKeyLink,
        controller: AtSearchKeyController,
        scope: {
            examples: '=',
            fields: '=',
            relatedFields: '=',
        },
    };
}

export default atSearchKey;
