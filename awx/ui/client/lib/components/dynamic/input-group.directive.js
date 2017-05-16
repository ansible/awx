function link (scope, el, attrs, controllers) {
    let formController = controllers[0];
    let dynamicController = controllers[1];
    el = el[0];

    dynamicController.init(scope, formController, el);
}

function atDynamicInputGroupController ($scope, $compile) {
    let vm = this || {};

    let state;
    let scope;
    let source;
    let form;
    let el;

    vm.init = (_scope_, _form_, _el_) => {
        form = _form_;
        scope = _scope_;
        el = _el_;

        scope.config.state = scope.config.state || {};
        state = scope.config.state;
        source = scope.config.source;

        $scope.$watch('config.source.state.value', vm.update);
    };

    vm.update = () => {
        if (!source.state.value || source.state.value === state.value) {
            return;
        }

        state.value = source.state.value;

        let inputs = scope.config.getInputs(source.state.value);
        let components = vm.createComponentConfigs(inputs);

        vm.insert(components);
        scope.config.components = components;
        vm.compile(components);
    };

    vm.createComponentConfigs = inputs => {
        let components = [];

        inputs.forEach((input, i) => {
            if (input.type === 'string') {
                if (input.secret) {
                    input.component = 'at-input-secret';
                } else if (input.multiline) {
                    input.component = 'at-input-textarea';
                } else {
                    input.component = 'at-input-text';
                }
            }

            let html = angular.element(`
                <${input.component}
                    col="${scope.col}"
                    config="${scope.config.reference}.components[${i}]">
                </${input.component}>
            `);

            components.push({
                options: input,
                html
            });
        });

        return components;
    };

    vm.insert = components => {
        components.forEach(component => el.appendChild(component.html[0]));
    };

    vm.compile = components => {
        components.forEach(component => $compile(component.html[0])(scope.$parent));
    };
}

atDynamicInputGroupController.$inject = ['$scope', '$compile'];

function atDynamicInputGroup (pathService) {
    return {
        restrict: 'E',
        replace: true,
        require: ['^^atForm', 'atDynamicInputGroup'],
        templateUrl: pathService.getPartialPath('components/dynamic/input-group'),
        controller: atDynamicInputGroupController,
        controllerAs: 'vm',
        link,
        scope: {
            config: '=',
            col: '@'
        }
    };
}

atDynamicInputGroup.$inject = ['PathService'];

export default atDynamicInputGroup;
