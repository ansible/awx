const templateUrl = require('./instance-list-policy.partial.html');

function InstanceListPolicyLink (scope, el, attrs, controllers) {
    const instancePolicyController = controllers[0];
    const formController = controllers[1];
    const models = scope.$resolve.resolvedModels;

    instancePolicyController.init(formController, models);
}


function InstanceListPolicyController ($scope, $state, strings) {
    const vm = this || {};
    let form;
    let instance;
    let instanceGroup;

    vm.init = (_form_, _models_) => {
        form = _form_;
        ({ instance, instanceGroup} = _models_);

        vm.strings = strings;
        vm.instanceGroupId = instanceGroup.get('id');
        vm.defaultParams = { page_size: '10', order_by: 'hostname' };

        if (vm.instanceGroupId === undefined) {
            vm.setInstances();
        } else {
            vm.setRelatedInstances();
        }
    };

    vm.setInstances = () => {
        vm.instances = instance.get('results').map(instance => {
            instance.isSelected = false;
            return instance;
        });
    };

    vm.setRelatedInstances = () => {
        vm.instanceGroupName = instanceGroup.get('name');
        vm.relatedInstances = instanceGroup.get('policy_instance_list');

        vm.instances = instance.get('results').map(instance => {
            instance.isSelected = vm.relatedInstances.includes(instance.hostname);
            return instance;
        });
    };

    $scope.$watch('vm.instances', function() {
        vm.selectedRows = _.filter(vm.instances, 'isSelected');
        vm.deselectedRows = _.filter(vm.instances, 'isSelected', false);
     }, true);

    vm.submit = () => {
        form.components
            .filter(component => component.category === 'input')
            .filter(component => component.state.id === 'policy_instance_list')
            .map(component => {
                component.state._value = vm.selectedRows;
            });

        $state.go("^.^");
    };
}

InstanceListPolicyController.$inject = [
    '$scope',
    '$state',
    'InstanceGroupsStrings'
];

function instanceListPolicy () {
    return {
        restrict: 'E',
        link: InstanceListPolicyLink,
        controller: InstanceListPolicyController,
        controllerAs: 'vm',
        require: ['instanceListPolicy', '^atForm'],
        templateUrl
    };
}

export default instanceListPolicy;
