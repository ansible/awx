function AddApplicationsController (models, $state, strings) {
    const vm = this || {};

    const { application, me, organization } = models;
    const omit = [
        'client_id',
        'client_secret',
        'created',
        'modified',
        'related',
        'skip_authorization',
        'summary_fields',
        'type',
        'url',
        'user'
    ];

    vm.mode = 'add';
    vm.strings = strings;
    vm.panelTitle = strings.get('add.PANEL_TITLE');

    vm.tab = {
        details: { _active: true },
        users: { _disabled: true }
    };

    vm.form = application.createFormSchema('post', { omit });

    vm.form.organization = {
        type: 'field',
        label: 'Organization',
        id: 'organization'
    };
    vm.form.description = {
        type: 'String',
        label: 'Description',
        id: 'description'
    };

    vm.form.disabled = !application.isCreatable();

    vm.form.organization._resource = 'organization';
    vm.form.organization._route = 'applications.add.organization';
    vm.form.organization._model = organization;
    vm.form.organization._placeholder = strings.get('inputs.ORGANIZATION_PLACEHOLDER');

    vm.form.name.required = true;
    vm.form.organization.required = true;

    delete vm.form.name.help_text;

    vm.form.save = data => {
        const hiddenData = {
            user: me.get('id')
        };

        const payload = _.merge(data, hiddenData);

        return application.request('post', { data: payload });
    };

    vm.form.onSaveSuccess = res => {
        $state.go('applications.edit', { application_id: res.data.id }, { reload: true });
    };
}

AddApplicationsController.$inject = [
    'resolvedModels',
    '$state',
    'ApplicationsStrings'
];

export default AddApplicationsController;
