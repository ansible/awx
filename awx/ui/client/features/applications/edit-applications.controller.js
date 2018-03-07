function EditApplicationsController (models, $state, strings, $scope) {
    const vm = this || {};

    const { me, application, organization } = models;

    const omit = [
        'authorization_grant_type',
        'client_id',
        'client_secret',
        'client_type',
        'created',
        'modified',
        'related',
        'skip_authorization',
        'summary_fields',
        'type',
        'url',
        'user'
    ];
    const isEditable = application.isEditable();

    vm.mode = 'edit';
    vm.strings = strings;
    vm.panelTitle = application.get('name');

    vm.tab = {
        details: {
            _active: true,
            _go: 'applications.edit',
            _params: { application_id: application.get('id') }
        },
        users: {
            _go: 'applications.edit.users',
            _params: { application_id: application.get('id') }
        }
    };

    $scope.$watch('$state.current.name', (value) => {
        if (/applications.edit.users/.test(value)) {
            vm.tab.details._active = false;
            vm.tab.users._active = true;
        } else {
            vm.tab.details._active = true;
            vm.tab.users._active = false;
        }
    });

    if (isEditable) {
        vm.form = application.createFormSchema('put', { omit });
    } else {
        vm.form = application.createFormSchema({ omit });
        vm.form.disabled = !isEditable;
    }

    vm.form.disabled = !isEditable;

    const isOrgAdmin = _.some(me.get('related.admin_of_organizations.results'), (org) => org.id === organization.get('id'));
    const isSuperuser = me.get('is_superuser');
    const isCurrentAuthor = Boolean(application.get('summary_fields.created_by.id') === me.get('id'));

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

    vm.form.organization._resource = 'organization';
    vm.form.organization._route = 'applications.edit.organization';
    vm.form.organization._model = organization;
    vm.form.organization._placeholder = strings.get('SELECT AN ORGANIZATION');

    // TODO: org not returned via api endpoint, check on this
    vm.form.organization._value = application.get('organization');

    vm.form.organization._disabled = true;
    if (isSuperuser || isOrgAdmin || (application.get('organization') === null && isCurrentAuthor)) {
        vm.form.organization._disabled = false;
    }

    vm.form.name.required = true;
    vm.form.organization.required = true;
    vm.form.redirect_uris.required = true;

    delete vm.form.name.help_text;

    vm.form.save = data => {
        const hiddenData = {
            authorization_grant_type: 'implicit',
            user: me.get('id'),
            client_type: 'public'
        };

        const payload = _.merge(data, hiddenData);

        return application.request('post', { data: payload });
    };
}

EditApplicationsController.$inject = [
    'resolvedModels',
    '$state',
    'ApplicationsStrings',
    '$scope'
];

export default EditApplicationsController;
