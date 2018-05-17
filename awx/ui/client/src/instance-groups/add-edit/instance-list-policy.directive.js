const templateUrl = require('./instance-list-policy.partial.html');

function InstanceListPolicyLink (scope, el, attrs, controllers) {
    const instancePolicyController = controllers[0];
    const formController = controllers[1];
    const models = scope.$resolve.resolvedModels;
    const Dataset = scope.$resolve.Dataset;

    instancePolicyController.init(formController, models, Dataset);
}

function InstanceListPolicyController ($scope, $state, strings) {
    const vm = this || {};
    let form;
    let instanceGroup;
    vm.strings = strings;

    vm.init = (_form_, _models_, Dataset) => {
        form = _form_;
        ({ instanceGroup } = _models_);

        vm.instanceGroupId = instanceGroup.get('id');

        $scope.list = {
            name: 'instances',
            iterator: 'instance'
        };
        $scope.instance_dataset = Dataset.data;
        $scope.instances = Dataset.data.results;

        if (vm.instanceGroupId === undefined) {
            vm.setInstances();
        } else {
            vm.setRelatedInstances();
        }
    };

    vm.setInstances = () => {
        $scope.instances = $scope.instances.map(instance => {
            instance.isSelected = false;
            return instance;
        });
    };

    vm.setRelatedInstances = () => {
        vm.relatedInstances = instanceGroup.get('policy_instance_list');

        $scope.instances = $scope.instances.map(instance => {
            instance.isSelected = vm.relatedInstances.includes(instance.hostname);
            return instance;
        });
    };

    $scope.$watch('instances', function() {
        vm.selectedRows = _.filter($scope.instances, 'isSelected');
        vm.deselectedRows = _.filter($scope.instances, 'isSelected', false);
     }, true);

    vm.submit = () => {
        form.components
            .filter(component => component.category === 'input')
            .filter(component => component.state.id === 'policy_instance_list')
            .forEach(component => {
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
