function EditController ($rootScope, $state, models, strings) {
    const vm = this || {};
    const { instanceGroup, instance } = models;

    $rootScope.breadcrumb.instance_group_name = instanceGroup.get('name');

    vm.mode = 'edit';
    vm.strings = strings;
    vm.panelTitle = instanceGroup.get('name');

    vm.tab = {
        details: {
            _active: true,
            _go: 'instanceGroups.edit',
            _params: { instance_group_id: instanceGroup.get('id') }
        },
        instances: {
            _go: 'instanceGroups.instances',
            _params: { instance_group_id: instanceGroup.get('id') }
        },
        jobs: {
            _go: 'instanceGroups.jobs',
            _params: { instance_group_id: instanceGroup.get('id') }
        }
    };

    vm.form = instanceGroup.createFormSchema('put');

    vm.form.disabled = !instanceGroup.has('options', 'actions.PUT');

    vm.form.name._disabled = instanceGroup.get('name') === 'tower';
    vm.form.policy_instance_list._lookupTags = true;
    vm.form.policy_instance_list._model = instance;
    vm.form.policy_instance_list._placeholder = "Policy Instance List";
    vm.form.policy_instance_list._resource = 'instances';
    vm.form.policy_instance_list._route = 'instanceGroups.edit.modal.instances';
    vm.form.policy_instance_list._value = instanceGroup.get('policy_instance_list');

    vm.form.save = data => {
        instanceGroup.unset('policy_instance_list');
        data.policy_instance_list = data.policy_instance_list.map(instance => instance.hostname || instance);
        return instanceGroup.request('put', { data });
    };

    vm.form.onSaveSuccess = res => {
        $state.go('instanceGroups.edit', { instance_group_id: res.data.id }, { reload: true });
    };
}

EditController.$inject = [
    '$rootScope',
    '$state',
    'resolvedModels',
    'InstanceGroupsStrings'
];

export default EditController;