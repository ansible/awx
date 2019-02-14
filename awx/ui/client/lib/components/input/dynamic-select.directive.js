const templateUrl = require('~components/input/dynamic-select.partial.html');

function atDynamicSelectLink (scope, element, attrs, controllers) {
    const [formController, inputController] = controllers;

    inputController.init(scope, element, formController);
}

function AtDynamicSelectController (baseInputController, CreateSelect2) {
    const vm = this || {};

    let scope;

    vm.init = (_scope_, _element_, form) => {
        baseInputController.call(vm, 'input', _scope_, _element_, form);
        scope = _scope_;
        CreateSelect2({
            element: `#${scope.state._formId}_${scope.state.id}_dynamic_select`,
            model: 'state._value',
            multiple: false,
            addNew: true,
            scope,
            options: 'state._data'
        });
        vm.check();
    };
}

AtDynamicSelectController.$inject = ['BaseInputController', 'CreateSelect2'];

function atDynamicSelect () {
    return {
        restrict: 'E',
        transclude: true,
        replace: true,
        require: ['^^at-form', 'atDynamicSelect'],
        templateUrl,
        controller: AtDynamicSelectController,
        controllerAs: 'vm',
        link: atDynamicSelectLink,
        scope: {
            state: '=',
            col: '@',
            tab: '@'
        }
    };
}

export default atDynamicSelect;
