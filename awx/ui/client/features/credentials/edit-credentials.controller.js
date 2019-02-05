function EditCredentialsController (
    models,
    $state,
    $scope,
    strings,
    componentsStrings,
    ConfigService
) {
    const vm = this || {};

    const { me, credential, credentialType, organization, isOrgCredAdmin } = models;

    const omit = ['user', 'team', 'inputs'];
    const isEditable = credential.isEditable();

    vm.mode = 'edit';
    vm.strings = strings;
    vm.panelTitle = credential.get('name');

    vm.tab = {
        details: {
            _active: true,
            _go: 'credentials.edit',
            _params: { credential_id: credential.get('id') }
        },
        permissions: {
            _go: 'credentials.edit.permissions',
            _params: { credential_id: credential.get('id') }
        }
    };

    $scope.$watch('$state.current.name', (value) => {
        if (/credentials.edit($|\.organization$|\.credentialType$)/.test(value)) {
            vm.tab.details._active = true;
            vm.tab.permissions._active = false;
        } else {
            vm.tab.permissions._active = true;
            vm.tab.details._active = false;
        }
    });

    $scope.$watch('organization', () => {
        if ($scope.organization) {
            vm.form.organization._idFromModal = $scope.organization;
        }
    });

    $scope.$watch('credential_type', () => {
        if ($scope.credential_type) {
            vm.form.credential_type._idFromModal = $scope.credential_type;
        }
    });

    // Only exists for permissions compatibility
    $scope.credential_obj = credential.get();

    if (isEditable) {
        vm.form = credential.createFormSchema('put', { omit });
    } else {
        vm.form = credential.createFormSchema({ omit });
        vm.form.disabled = !isEditable;
    }

    const isOrgAdmin = _.some(me.get('related.admin_of_organizations.results'), (org) => org.id === organization.get('id'));
    const isSuperuser = me.get('is_superuser');
    const isCurrentAuthor = Boolean(credential.get('summary_fields.created_by.id') === me.get('id'));
    vm.form.organization._disabled = true;

    if (isSuperuser || isOrgAdmin || isOrgCredAdmin || (credential.get('organization') === null && isCurrentAuthor)) {
        vm.form.organization._disabled = false;
    }

    vm.form.organization._resource = 'organization';
    vm.form.organization._model = organization;
    vm.form.organization._route = 'credentials.edit.organization';
    vm.form.organization._value = credential.get('summary_fields.organization.id');
    vm.form.organization._displayValue = credential.get('summary_fields.organization.name');
    vm.form.organization._placeholder = strings.get('inputs.ORGANIZATION_PLACEHOLDER');

    vm.form.credential_type._resource = 'credential_type';
    vm.form.credential_type._model = credentialType;
    vm.form.credential_type._route = 'credentials.edit.credentialType';
    vm.form.credential_type._value = credentialType.get('id');
    vm.form.credential_type._displayValue = credentialType.get('name');
    vm.form.credential_type._placeholder = strings.get('inputs.CREDENTIAL_TYPE_PLACEHOLDER');

    const gceFileInputSchema = {
        id: 'gce_service_account_key',
        type: 'file',
        label: strings.get('inputs.GCE_FILE_INPUT_LABEL'),
        help_text: strings.get('inputs.GCE_FILE_INPUT_HELP_TEXT'),
    };

    let gceFileInputPreEditValues;

    vm.form.inputs = {
        _get () {
            let fields;

            credentialType.mergeInputProperties();

            if (credentialType.get('id') === credential.get('credential_type')) {
                fields = credential.assignInputGroupValues(credentialType.get('inputs.fields'));
            } else {
                fields = credentialType.get('inputs.fields');
            }

            if (credentialType.get('name') === 'Google Compute Engine') {
                fields.splice(2, 0, gceFileInputSchema);

                $scope.$watch(`vm.form.${gceFileInputSchema.id}._value`, vm.gceOnFileInputChanged);
                $scope.$watch('vm.form.ssh_key_data._isBeingReplaced', vm.gceOnReplaceKeyChanged);
            } else if (credentialType.get('name') === 'Machine') {
                const apiConfig = ConfigService.get();
                const become = fields.find((field) => field.id === 'become_method');
                become._isDynamic = true;
                become._choices = Array.from(apiConfig.become_methods, method => method[0]);
                // Add the value to the choices if it doesn't exist in the preset list
                if (become._value && become._value !== '') {
                    const optionMatches = become._choices
                        .findIndex((option) => option === become._value);
                    if (optionMatches === -1) {
                        become._choices.push(become._value);
                    }
                }
            }

            return fields;
        },
        _source: vm.form.credential_type,
        _reference: 'vm.form.inputs',
        _key: 'inputs'
    };

    /**
     * If a credential's `credential_type` is changed while editing, the inputs associated with
     * the old type need to be cleared before saving the inputs associated with the new type.
     * Otherwise inputs are merged together making the request invalid.
     */
    vm.form.save = data => {
        data.user = me.get('id');
        credential.unset('inputs');

        if (_.get(data.inputs, gceFileInputSchema.id)) {
            delete data.inputs[gceFileInputSchema.id];
        }

        const filteredInputs = _.omit(data.inputs, (value) => value === '');
        data.inputs = filteredInputs;

        return credential.request('put', { data });
    };

    vm.form.onSaveSuccess = () => {
        $state.go('credentials.edit', { credential_id: credential.get('id') }, { reload: true });
    };

    vm.gceOnReplaceKeyChanged = value => {
        vm.form[gceFileInputSchema.id]._disabled = !value;
    };

    vm.gceOnFileInputChanged = (value, oldValue) => {
        if (value === oldValue) return;

        const gceFileIsLoaded = !!value;
        const gceFileInputState = vm.form[gceFileInputSchema.id];
        const { obj, error } = vm.gceParseFileInput(value);

        gceFileInputState._isValid = !error;
        gceFileInputState._message = error ? componentsStrings.get('message.INVALID_INPUT') : '';

        vm.form.project._disabled = gceFileIsLoaded;
        vm.form.username._disabled = gceFileIsLoaded;
        vm.form.ssh_key_data._disabled = gceFileIsLoaded;
        vm.form.ssh_key_data._displayHint = !vm.form.ssh_key_data._disabled;

        if (gceFileIsLoaded) {
            gceFileInputPreEditValues = Object.assign({}, {
                project: vm.form.project._value,
                ssh_key_data: vm.form.ssh_key_data._value,
                username: vm.form.username._value
            });
            vm.form.project._value = _.get(obj, 'project_id', '');
            vm.form.ssh_key_data._value = _.get(obj, 'private_key', '');
            vm.form.username._value = _.get(obj, 'client_email', '');
        } else {
            vm.form.project._value = gceFileInputPreEditValues.project;
            vm.form.ssh_key_data._value = gceFileInputPreEditValues.ssh_key_data;
            vm.form.username._value = gceFileInputPreEditValues.username;
        }
    };

    vm.gceParseFileInput = value => {
        let obj;
        let error;

        try {
            obj = angular.fromJson(value);
        } catch (err) {
            error = err;
        }

        return { obj, error };
    };
}

EditCredentialsController.$inject = [
    'resolvedModels',
    '$state',
    '$scope',
    'CredentialsStrings',
    'ComponentsStrings',
    'ConfigService'
];

export default EditCredentialsController;
