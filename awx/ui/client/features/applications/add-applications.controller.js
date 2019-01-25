function AddApplicationsController (models, $state, strings, $scope, Alert, $filter, i18n) {
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
        label: i18n._('Organization'),
        id: 'organization'
    };
    vm.form.description = {
        type: 'String',
        label: i18n._('Description'),
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
        if (res.data && res.data.client_id) {
            const name = res.data.name ?
                `<div class="PopupModal">
                    <div class="PopupModal-label">
                        ${strings.get('add.NAME_LABEL')}
                    </div>
                    <div class="PopupModal-value">
                        ${$filter('sanitize')(res.data.name)}
                    </div>
                </div>` : '';
            const clientId = res.data.client_id ?
                `<div class="PopupModal">
                    <div class="PopupModal-label">
                        ${strings.get('add.CLIENT_ID_LABEL')}
                    </div>
                    <div class="PopupModal-value">
                        ${res.data.client_id}
                    </div>
                </div>` : '';
            const clientSecret = res.data.client_secret ?
                `<div class="PopupModal">
                    <div class="PopupModal-label">
                        ${strings.get('add.CLIENT_SECRECT_LABEL')}
                    </div>
                    <div class="PopupModal-value">
                        ${res.data.client_secret}
                    </div>
                </div>` : '';

            Alert(strings.get('add.MODAL_HEADER'), `
                ${name}
                ${clientId}
                ${clientSecret}
            `, null, null, null, null, null, true);
        }
        $state.go('applications.edit', { application_id: res.data.id }, { reload: true });
    };

    $scope.$watch('organization', () => {
        if ($scope.organization) {
            vm.form.organization._idFromModal = $scope.organization;
        }
    });
}

AddApplicationsController.$inject = [
    'resolvedModels',
    '$state',
    'ApplicationsStrings',
    '$scope',
    'Alert',
    '$filter',
    'i18n'
];

export default AddApplicationsController;
