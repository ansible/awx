function AddController ($scope, $state, models, strings) {
    const vm = this || {};
    const { instanceGroup, instance } = models;

    vm.mode = 'add';
    vm.strings = strings;
    vm.panelTitle = strings.get('state.ADD_BREADCRUMB_LABEL');

    vm.tab = {
        details: { _active: true },
        instances: {_disabled: true },
        jobs: {_disabled: true }
    };

    vm.form = instanceGroup.createFormSchema('post');

    // Default policy instance percentage value is 0
    vm.form.policy_instance_percentage._value = 0;

    vm.form.policy_instance_list._lookupTags = true;
    vm.form.policy_instance_list._model = instance;
    vm.form.policy_instance_list._placeholder = "Policy Instance List";
    vm.form.policy_instance_list._resource = 'instances';
    vm.form.policy_instance_list._route = 'instanceGroups.add.modal.instances';
    vm.form.policy_instance_list._value = [];

    vm.form.save = data => {
        data.policy_instance_list = data.policy_instance_list.map(instance => instance.hostname);
        return instanceGroup.request('post', { data });
    };

    vm.form.onSaveSuccess = res => {
        $state.go('instanceGroups.edit', { instance_group_id: res.data.id }, { reload: true });
    };
}

AddController.$inject = [
    '$scope',
    '$state',
    'resolvedModels',
    'InstanceGroupsStrings'
];

export default AddController;