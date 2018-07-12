function EditApplicationsController (models, $state, strings, $scope) {
    const vm = this || {};

    const { me, application, organization } = models;

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

    $scope.$watch('organization', () => {
        if ($scope.organization) {
            vm.form.organization._idFromModal = $scope.organization;
        }
    });

    if (isEditable) {
        vm.form = application.createFormSchema('put', { omit });
    } else {
        vm.form = application.createFormSchema({ omit });
        vm.form.disabled = !isEditable;
    }

    vm.form.disabled = !isEditable;

    vm.form.name.required = true;

    const isOrgAdmin = _.some(me.get('related.admin_of_organizations.results'), (org) => org.id === organization.get('id'));
    const isSuperuser = me.get('is_superuser');
    const isCurrentAuthor = Boolean(application.get('summary_fields.created_by.id') === me.get('id'));
    vm.form.organization._disabled = true;

    if (isSuperuser || isOrgAdmin || (application.get('organization') === null && isCurrentAuthor)) {
        vm.form.organization._disabled = false;
    }

    vm.form.organization._resource = 'organization';
    vm.form.organization._model = organization;
    vm.form.organization._route = 'applications.edit.organization';
    vm.form.organization._value = application.get('summary_fields.organization.id');
    vm.form.organization._displayValue = application.get('summary_fields.organization.name');
    vm.form.organization._placeholder = strings.get('inputs.ORGANIZATION_PLACEHOLDER');
    vm.form.organization.required = true;

    delete vm.form.name.help_text;

    vm.form.save = data => {
        const hiddenData = {
            user: me.get('id')
        };

        const payload = _.merge(data, hiddenData);

        return application.request('put', { data: payload });
    };

    vm.form.onSaveSuccess = () => {
        $state.go('applications.edit', { application_id: application.get('id') }, { reload: true });
    };
}

EditApplicationsController.$inject = [
    'resolvedModels',
    '$state',
    'ApplicationsStrings',
    '$scope'
];

export default EditApplicationsController;
