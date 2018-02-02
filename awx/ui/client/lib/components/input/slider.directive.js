const templateUrl = require('~components/input/slider.partial.html');

function atInputSliderLink (scope, element, attrs, controllers) {
    const [formController, inputController] = controllers;

    inputController.init(scope, element, formController);
}

function atInputSliderController (baseInputController) {
    const vm = this || {};

    vm.init = (_scope_, _element_, form) => {
        baseInputController.call(vm, 'input', _scope_, _element_, form);

        vm.check();
    };
}

atInputSliderController.$inject = ['BaseInputController'];

function atInputSlider () {
    return {
        restrict: 'E',
        require: ['^^atForm', 'atInputSlider'],
        replace: true,
        templateUrl,
        controller: atInputSliderController,
        controllerAs: 'vm',
        link: atInputSliderLink,
        scope: {
            state: '=?',
            col: '@',
            tab: '@'
        }
    };
}

export default atInputSlider;
