function AddController ($state, models, strings) {
    const vm = this || {};
    const { instanceGroup } = models;

    vm.mode = 'add';
    vm.strings = strings;
    vm.panelTitle = strings.get('state.ADD_BREADCRUMB_LABEL');

    vm.docs = {
        url: 'https://docs.ansible.com/ansible-tower/latest/html/userguide/instance_groups.html',
        help_text: vm.strings.get('tooltips.IG_DOCS_HELP_TEXT')
    };

    vm.tab = {
        details: { _active: true },
        instances: {_disabled: true },
        jobs: {_disabled: true }
    };

    vm.form = instanceGroup.createFormSchema('post');

    // Default policy instance percentage value is 0
    vm.form.policy_instance_percentage._value = 0;

    vm.form.save = data => {
        return instanceGroup.request('post', { data });
    };

    vm.form.onSaveSuccess = res => {
        $state.go('instanceGroups.edit', { instance_group_id: res.data.id }, { reload: true });
    };
}

AddController.$inject = [
    '$state',
    'resolvedModels',
    'InstanceGroupsStrings'
];

export default AddController;