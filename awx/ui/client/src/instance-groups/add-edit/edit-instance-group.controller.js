function EditController ($rootScope, $state, models, strings) {
    const vm = this || {};
    const { instanceGroup } = models;

    if (instanceGroup.get('is_containerized')) {
        return $state.go(
            'instanceGroups.editContainerGroup',
            { instance_group_id: instanceGroup.get('id') },
            { reload: true }
        );
    }

    $rootScope.breadcrumb.instance_group_name = instanceGroup.get('name');

    vm.mode = 'edit';
    vm.strings = strings;
    vm.panelTitle = instanceGroup.get('name');

    vm.docs = {
        url: 'https://docs.ansible.com/ansible-tower/latest/html/userguide/instance_groups.html',
        help_text: vm.strings.get('tooltips.IG_DOCS_HELP_TEXT')
    };

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

    vm.form.save = data => {
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
