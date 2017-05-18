function link (scope, el, attrs, controllers) {
    let dynamicController = controllers[0];
    let element = el[0].getElementsByClassName('at-DynamicInputGroup-container')[0];

    dynamicController.init(scope, element);
}

function AtDynamicInputGroupController ($scope, $compile) {
    let vm = this || {};

    let scope;
    let state;
    let source;
    let element;

    vm.init = (_scope_, _element_) => {
        scope = _scope_;
        element = _element_;
        state = scope.state || {};
        source = state.source;

        $scope.$watch('state.source.value', vm.update);
    };

    vm.isValidSource = () => {
        if (!source.value || source.value === state.value) {
            return false;
        }
        
        return true;
    };

    vm.update = () => {
        if (!vm.isValidSource()) {
            return;
        }

        vm.clear();

        state.value = source.value;

        let inputs = state.getInputs(source.value);
        let components = vm.createComponentConfigs(inputs);

        vm.insert(components);
        state.components = components;
        vm.compile(components);
    };

    vm.createComponentConfigs = inputs => {
        let components = [];

        inputs.forEach((input, i) => {
            if (input.type === 'string') {
                if (input.secret && input.multiline) {
                    input.component = 'at-input-textarea';
                } else if (input.secret) {
                    input.component = 'at-input-secret';
                } else if (input.multiline) {
                    input.component = 'at-input-textarea';
                } else {
                    input.component = 'at-input-text';
                }
            }

            components.push(Object.assign({
                element: vm.createElement(input, i)
            }, input));
        });

        return components;
    };

    vm.createElement = (input, index) => {
        let tabindex = Number(scope.tab) + index;

        let element =
            `<${input.component} col="${scope.col}" tab="${tabindex}"
                state="${state.reference}.components[${index}]">
            </${input.component}>`;

        return angular.element(element);
    };

    vm.insert = components => {
        let group = document.createElement('div');
        let divider = angular.element(`<div class="at-DynamicInputGroup-divider"></div>`)[0];

        for (let i = 0; i < components.length; i++) {
            if (i !== 0 && (i % (12 / scope.col)) === 0) {
                group.appendChild(divider);
            }

            group.appendChild(components[i].element[0]);
        }

        element.appendChild(group);
    };

    vm.compile = components => {
        components.forEach(component => $compile(component.element[0])(scope.$parent));
    };

    vm.clear = () => {
        element.innerHTML = '';
    };
}

AtDynamicInputGroupController.$inject = ['$scope', '$compile'];

function atDynamicInputGroup (pathService) {
    return {
        restrict: 'E',
        replace: true,
        transclude: true,
        require: ['atDynamicInputGroup'],
        templateUrl: pathService.getPartialPath('components/dynamic/input-group'),
        controller: AtDynamicInputGroupController,
        controllerAs: 'vm',
        link,
        scope: {
            state: '=',
            col: '@',
            tab: '@'
        }
    };
}

atDynamicInputGroup.$inject = ['PathService'];

export default atDynamicInputGroup;
