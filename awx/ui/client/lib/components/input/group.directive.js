const templateUrl = require('~components/input/group.partial.html');

function atInputGroupLink (scope, el, attrs, controllers) {
    const groupController = controllers[0];
    const formController = controllers[1];
    const element = el[0].getElementsByClassName('at-InputGroup-container')[0];

    groupController.init(scope, formController, element);
}

function AtInputGroupController ($scope, $compile) {
    const vm = this || {};

    let form;
    let scope;
    let state;
    let source;
    let element;
    let formId;

    vm.init = (_scope_, _form_, _element_) => {
        form = _form_;
        scope = _scope_;
        element = _element_;
        state = scope.state || {};
        source = state._source;
        ({ formId } = scope);

        $scope.$watch('state._source._value', vm.update);
    };

    vm.isValidSource = () => {
        if (!source._value || source._value === state._value) {
            return false;
        }

        return true;
    };

    vm.update = () => {
        if (state._group) {
            vm.clear();
        }

        if (!vm.isValidSource()) {
            return;
        }

        state._value = source._value;

        const inputs = state._get(form);
        const group = vm.createComponentConfigs(inputs);

        vm.insert(group);
        state._group = group;
    };

    vm.createComponentConfigs = inputs => {
        const group = [];

        if (inputs) {
            inputs.forEach((input, i) => {
                input = Object.assign(input, vm.getComponentType(input));

                group.push(Object.assign({
                    _element: vm.createComponent(input, i),
                    _key: 'inputs',
                    _group: true,
                    _groupIndex: i,
                    _onInputLookup: state._onInputLookup,
                    _onRemoveTag: state._onRemoveTag,
                }, input));
            });
        }

        return group;
    };

    vm.getComponentType = input => {
        const config = {
            _formId: formId
        };

        if (input.type === 'string') {
            if (input._isDynamic) {
                config._component = 'at-dynamic-select';
                config._format = 'array';
                config._data = input._choices;
                config._exp = 'choice for (index, choice) in state._data';
                config._isDynamic = true;
            } else if (!input.multiline) {
                if (input.secret) {
                    config._component = 'at-input-secret';
                } else {
                    config._component = 'at-input-text';
                }
            } else {
                config._expand = true;

                if (input.secret) {
                    config._component = 'at-input-textarea-secret';
                    input.format = 'ssh_private_key';
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
        } else if (input.type === 'file') {
            config._component = 'at-input-file';
        }

        if (input.choices) {
            config._component = 'at-input-select';
            config._format = 'array';
            config._data = input.choices;
            config._exp = 'choice for (index, choice) in state._data';
        }

        if (!config._component) {
            const preface = vm.strings.get('group.UNSUPPORTED_ERROR_PREFACE');
            throw new Error(`${preface}: ${input.type}`);
        }

        return config;
    };

    vm.insert = group => {
        const container = document.createElement('div');
        container.className = 'row';
        let col = 1;
        const colPerRow = 12 / scope.col;
        let isDivided = true;

        group.forEach((input, i) => {
            if (input._expand && !isDivided) {
                container.appendChild(vm.createDivider()[0]);
            }

            container.appendChild(input._element[0]);

            if ((input._expand || col % colPerRow === 0) && i !== group.length - 1) {
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
        const tabindex = Number(scope.tab) + index;
        const col = input._expand ? 12 : scope.col;
        const component = angular.element(`<${input._component} col="${col}" tab="${tabindex}"
                state="${state._reference}._group[${index}]" id="${formId}_${input.id}_group">
            </${input._component}>`);

        $compile(component)(scope.$parent);
        return component;
    };

    vm.createDivider = () => {
        const divider = angular.element('<at-divider></at-divider>');
        $compile(divider[0])(scope.$parent);

        return divider;
    };

    vm.clear = () => {
        form.deregisterInputGroup(state._group);
        element.innerHTML = '';
        state._group = undefined;
        state._value = undefined;
    };
}

AtInputGroupController.$inject = ['$scope', '$compile'];

function atInputGroup () {
    return {
        restrict: 'E',
        replace: true,
        transclude: true,
        require: ['atInputGroup', '^^atForm'],
        templateUrl,
        controller: AtInputGroupController,
        controllerAs: 'vm',
        link: atInputGroupLink,
        scope: {
            state: '=',
            col: '@',
            tab: '@',
            formId: '@'
        }
    };
}

export default atInputGroup;
