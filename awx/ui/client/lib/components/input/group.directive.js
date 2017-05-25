function atInputGroupLink (scope, el, attrs, controllers) {
    let groupController = controllers[0];
    let formController = controllers[1];
    let element = el[0].getElementsByClassName('at-InputGroup-container')[0];

    groupController.init(scope, formController, element);
}

function AtInputGroupController ($scope, $compile) {
    let vm = this || {};

    let form;
    let scope;
    let state;
    let source;
    let element;

    vm.init = (_scope_, _form_, _element_) => {
        form = _form_;
        scope = _scope_;
        element = _element_;
        state = scope.state || {};
        source = state._source;

        $scope.$watch('state._source._value', vm.update);
    };

    vm.isValidSource = () => {
        if (!source._value || source._value === state._value) {
            return false;
        }
        
        return true;
    };

    vm.update = () => {
        if (!vm.isValidSource()) {
            return;
        }

        if (state._group) {
            vm.clear();
        }

        state._value = source._value;

        let inputs = state._get(source._value);
        let group = vm.createComponentConfigs(inputs);

        vm.insert(group);
        state._group = group;
        vm.compile(group);
    };

    vm.createComponentConfigs = inputs => {
        let group = [];

        inputs.forEach((input, i) => {
            if (input.type === 'string') {
                if (input.secret && input.multiline) {
                    input._component = 'at-input-textarea';
                } else if (input.secret) {
                    input._component = 'at-input-secret';
                } else if (input.multiline) {
                    input._component = 'at-input-textarea';
                } else {
                    input._component = 'at-input-text';
                }
            }

            group.push(Object.assign({
                _element: vm.createElement(input, i),
                _key: 'inputs',
                _group: true
            }, input));
        });

        return group;
    };

    vm.createElement = (input, index) => {
        let tabindex = Number(scope.tab) + index;

        let element =
            `<${input._component} col="${scope.col}" tab="${tabindex}"
                state="${state._reference}._group[${index}]">
            </${input._component}>`;

        return angular.element(element);
    };

    vm.insert = group => {
        let container = document.createElement('div');
        let divider = angular.element(`<div class="at-InputGroup-divider"></div>`)[0];

        for (let i = 0; i < group.length; i++) {
            if (i !== 0 && (i % (12 / scope.col)) === 0) {
                container.appendChild(divider);
            }

            container.appendChild(group[i]._element[0]);
        }

        element.appendChild(container);
    };

    vm.compile = group => {
        group.forEach(component => $compile(component._element[0])(scope.$parent));
    };

    vm.clear = () => {
        form.deregisterInputGroup(state._group);
        element.innerHTML = '';
    };
}

AtInputGroupController.$inject = ['$scope', '$compile'];

function atInputGroup (pathService) {
    return {
        restrict: 'E',
        replace: true,
        transclude: true,
        require: ['atInputGroup', '^^atForm'],
        templateUrl: pathService.getPartialPath('components/input/group'),
        controller: AtInputGroupController,
        controllerAs: 'vm',
        link: atInputGroupLink,
        scope: {
            state: '=',
            col: '@',
            tab: '@'
        }
    };
}

atInputGroup.$inject = ['PathService'];

export default atInputGroup;
