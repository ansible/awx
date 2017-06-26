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
    };

    vm.createComponentConfigs = inputs => {
        let group = [];

        inputs.forEach((input, i) => {
            input = Object.assign(input, vm.getComponentType(input));

            group.push(Object.assign({
                _element: vm.createComponent(input, i),
                _key: 'inputs',
                _group: true,
                _groupIndex: i
            }, input));
        });

        return group;
    };

    vm.getComponentType = input => {
        let config = {};

        if (input.type === 'string') {
            if (!input.multiline) {
                if (input.secret) {
                    config._component = 'at-input-secret';
                } else {
                    config._component = 'at-input-text';
                }
            } else {
                config._expand = true;

                if (input.secret) {
                    config._component = 'at-input-textarea-secret';
                } else {
                    config._component = 'at-input-textarea';
                }
            }

            if (input.format === 'ssh_private_key') {
                config._format = 'ssh-key';
            }
        } else if (input.type === 'number') {
            config._component = 'at-input-number';
        } else if (input.type === 'boolean') {
            config._component = 'at-input-checkbox';
        } else if (input.choices) {
            config._component = 'at-input-select';
            config._format = 'array';
            config._data = input.choices;
            config._exp = 'index as choice for (index, choice) in state._data';
        } else {
            throw new Error('Unsupported input type: ' + input.type)
        }

        return config;
    };

    vm.insert = group => {
        let container = document.createElement('div');
        let col = 1;
        let colPerRow = 12 / scope.col;
        let isDivided = true;

        group.forEach((input, i) => {
            if (input._expand && !isDivided) {
                container.appendChild(vm.createDivider()[0]);
            }

            container.appendChild(input._element[0]);

            if ((input._expand || col % colPerRow === 0) && i !== group.length -1) {
                container.appendChild(vm.createDivider()[0]);
                isDivided = true;
                col = 0;
            } else {
                isDivided = false;
            }

            col++;
        });

        element.appendChild(container);
    };

    vm.createComponent = (input, index) => {
        let tabindex = Number(scope.tab) + index;
        let col = input._expand ? 12 : scope.col;
        let component = angular.element(
            `<${input._component} col="${col}" tab="${tabindex}"
                state="${state._reference}._group[${index}]">
            </${input._component}>`
        );

        $compile(component)(scope.$parent)

        return component;
    };

    vm.createDivider = () => {
        let divider = angular.element('<at-divider></at-divider>');
        $compile(divider[0])(scope.$parent);

        return divider;
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
