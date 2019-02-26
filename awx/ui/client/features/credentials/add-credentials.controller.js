/* eslint camelcase: 0 */
/* eslint arrow-body-style: 0 */
function AddCredentialsController (
    models,
    $state,
    $scope,
    strings,
    componentsStrings,
    ConfigService,
    ngToast,
    Wait,
    $filter,
    CredentialType,
) {
    const vm = this || {};

    const { me, credential, credentialType, organization } = models;

    vm.mode = 'add';
    vm.strings = strings;
    vm.panelTitle = strings.get('add.PANEL_TITLE');

    vm.tab = {
        details: { _active: true },
        permissions: { _disabled: true }
    };

    vm.form = credential.createFormSchema('post', {
        omit: ['user', 'team', 'inputs']
    });

    vm.form._formName = 'credential';

    vm.form.disabled = !credential.isCreatable();

    vm.form.organization._resource = 'organization';
    vm.form.organization._route = 'credentials.add.organization';
    vm.form.organization._model = organization;
    vm.form.organization._placeholder = strings.get('inputs.ORGANIZATION_PLACEHOLDER');

    vm.form.credential_type._resource = 'credential_type';
    vm.form.credential_type._route = 'credentials.add.credentialType';
    vm.form.credential_type._model = credentialType;
    vm.form.credential_type._placeholder = strings.get('inputs.CREDENTIAL_TYPE_PLACEHOLDER');
    vm.isTestable = credentialType.get('kind') === 'external';

    vm.inputSources = {
        field: null,
        credentialId: null,
        credentialTypeId: null,
        credentialTypeName: null,
        tabs: {
            credential: {
                _active: true,
                _disabled: false,
            },
            metadata: {
                _active: false,
                _disabled: false,
            }
        },
        metadata: {},
        form: {
            inputs: {
                _get: () => vm.inputSources.metadata,
                _reference: 'vm.form.inputs',
                _key: 'inputs',
                _source: { _value: {} },
            }
        },
        items: [],
    };
    vm.externalTest = {
        metadata: null,
        form: {
            inputs: {
                _get: () => vm.externalTest.metadata,
                _reference: 'vm.form.inputs',
                _key: 'inputs',
                _source: { _value: {} },
            }
        },
    };

    const gceFileInputSchema = {
        id: 'gce_service_account_key',
        type: 'file',
        label: strings.get('inputs.GCE_FILE_INPUT_LABEL'),
        help_text: strings.get('inputs.GCE_FILE_INPUT_HELP_TEXT'),
    };

    let gceFileInputPreEditValues;

    vm.form.inputs = {
        _get: ({ getSubmitData }) => {
            credentialType.mergeInputProperties();

            let fields = credentialType.get('inputs.fields');

            if (credentialType.get('name') === 'Google Compute Engine') {
                fields.splice(2, 0, gceFileInputSchema);
                $scope.$watch(`vm.form.${gceFileInputSchema.id}._value`, vm.gceOnFileInputChanged);
            } else if (credentialType.get('name') === 'Machine') {
                const apiConfig = ConfigService.get();
                const become = fields.find((field) => field.id === 'become_method');
                become._isDynamic = true;
                become._choices = Array.from(apiConfig.become_methods, method => method[0]);
            }
            vm.isTestable = credentialType.get('kind') === 'external';
            vm.getSubmitData = getSubmitData;

            fields = fields.map((field) => {
                if (credentialType.get('kind') !== 'external') {
                    field.tagMode = true;
                }
                return field;
            });

            return fields;
        },
        _onRemoveTag ({ id }) {
            vm.onInputSourceClear(id);
        },
        _onInputLookup ({ id }) {
            vm.onInputSourceOpen(id);
        },
        _source: vm.form.credential_type,
        _reference: 'vm.form.inputs',
        _key: 'inputs'
    };

    vm.onInputSourceClear = (field) => {
        vm.form[field].tagMode = true;
        vm.form[field].asTag = false;
    };

    vm.setTab = (name) => {
        const metaIsActive = name === 'metadata';
        vm.inputSources.tabs.credential._active = !metaIsActive;
        vm.inputSources.tabs.credential._disabled = false;
        vm.inputSources.tabs.metadata._active = metaIsActive;
        vm.inputSources.tabs.metadata._disabled = false;
    };

    vm.unsetTabs = () => {
        vm.inputSources.tabs.credential._active = false;
        vm.inputSources.tabs.credential._disabled = false;
        vm.inputSources.tabs.metadata._active = false;
        vm.inputSources.tabs.metadata._disabled = false;
    };

    vm.onInputSourceOpen = (field) => {
        vm.inputSources.field = field;
        vm.setTab('credential');
        const sourceItem = vm.inputSources.items
            .find(({ input_field_name }) => input_field_name === field);
        if (sourceItem) {
            const { source_credential, summary_fields } = sourceItem;
            const { source_credential: { credential_type_id } } = summary_fields;
            vm.inputSources.credentialId = source_credential;
            vm.inputSources.credentialTypeId = credential_type_id;
            vm.inputSources._value = credential_type_id;
        }
    };

    vm.onInputSourceClose = () => {
        vm.inputSources.field = null;
        vm.inputSources.metadata = null;
        vm.unsetTabs();
    };

    vm.onInputSourceNext = () => {
        const { field, credentialId, credentialTypeId } = vm.inputSources;
        Wait('start');
        new CredentialType('get', credentialTypeId)
            .then(model => {
                model.mergeInputProperties('metadata');
                vm.inputSources.metadata = model.get('inputs.metadata');
                vm.inputSources.credentialTypeName = model.get('name');
                const [metavals] = vm.inputSources.items
                    .filter(({ input_field_name }) => input_field_name === field)
                    .filter(({ source_credential }) => source_credential === credentialId)
                    .map(({ metadata }) => metadata);
                Object.keys(metavals || {}).forEach(key => {
                    const obj = vm.inputSources.metadata.find(o => o.id === key);
                    if (obj) obj._value = metavals[key];
                });
                vm.setTab('metadata');
            })
            .finally(() => Wait('stop'));
    };

    vm.onInputSourceSelect = () => {
        const { field, credentialId } = vm.inputSources;
        vm.inputSources.items = vm.inputSources.items
            .filter(({ input_field_name }) => input_field_name !== field)
            .concat([{
                input_field_name: field,
                source_credential: credentialId,
                target_credential: credential.get('id'),
            }]);
        vm.inputSources.field = null;
        vm.inputSources.metadata = null;
        vm.unsetTabs();
    };

    vm.onInputSourceTabSelect = (name) => {
        if (name === 'metadata') {
            vm.onInputSourceNext();
        } else {
            vm.setTab('credential');
        }
    };

    vm.onInputSourceRowClick = ({ id, credential_type }) => {
        vm.inputSources.credentialId = id;
        vm.inputSources.credentialTypeId = credential_type;
        vm.inputSources._value = credential_type;
    };

    vm.onInputSourceTest = () => {
        const metadata = Object.assign({}, ...vm.inputSources.form.inputs._group
            .filter(({ _value }) => _value !== undefined)
            .map(({ id, _value }) => ({ [id]: _value })));
        const name = $filter('sanitize')(vm.inputSources.credentialTypeName);
        const endpoint = `${vm.inputSources.credentialId}/test/`;

        return vm.runTest({ name, model: credential, endpoint, data: { metadata } });
    };

    vm.onExternalTestClick = () => {
        credentialType.mergeInputProperties('metadata');
        vm.externalTest.metadata = credentialType.get('inputs.metadata');
    };

    vm.onExternalTestClose = () => {
        vm.externalTest.metadata = null;
    };

    vm.onExternalTest = () => {
        const name = $filter('sanitize')(credentialType.get('name'));
        const { inputs } = vm.getSubmitData();
        const metadata = Object.assign({}, ...vm.externalTest.form.inputs._group
            .filter(({ _value }) => _value !== undefined)
            .map(({ id, _value }) => ({ [id]: _value })));

        let model;
        if (credential.get('credential_type') !== credentialType.get('id')) {
            model = credentialType;
        } else {
            model = credential;
        }

        const endpoint = `${model.get('id')}/test/`;
        return vm.runTest({ name, model, endpoint, data: { inputs, metadata } });
    };
    vm.form.secondary = vm.onExternalTestClick;

    vm.runTest = ({ name, model, endpoint, data: { inputs, metadata } }) => {
        return model.http.post({ url: endpoint, data: { inputs, metadata }, replace: false })
            .then(() => {
                ngToast.success({
                    content: vm.buildTestNotificationContent({
                        name,
                        icon: 'fa-check-circle',
                        msg: strings.get('edit.TEST_PASSED'),
                    }),
                    dismissButton: false,
                    dismissOnTimeout: true
                });
            })
            .catch(({ data }) => {
                const msg = data.inputs
                    ? `${$filter('sanitize')(data.inputs)}`
                    : strings.get('edit.TEST_FAILED');
                ngToast.danger({
                    content: vm.buildTestNotificationContent({
                        name,
                        msg,
                        icon: 'fa-exclamation-triangle'
                    }),
                    dismissButton: false,
                    dismissOnTimeout: true
                });
            });
    };

    vm.buildTestNotificationContent = ({ name, msg, icon }) => (
        `<div class="Toast-wrapper">
            <div class="Toast-icon">
                <i class="fa ${icon} Toast-successIcon"></i>
            </div>
            <div>
                <b>${name}:</b> ${msg}
            </div>
        </div>`
    );

    vm.form.save = data => {
        data.user = me.get('id');

        if (_.get(data.inputs, gceFileInputSchema.id)) {
            delete data.inputs[gceFileInputSchema.id];
        }

        const filteredInputs = _.omit(data.inputs, (value) => value === '');
        data.inputs = filteredInputs;

        return credential.request('post', { data });
    };

    vm.form.onSaveSuccess = res => {
        $state.go('credentials.edit', { credential_id: res.data.id }, { reload: true });
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
}

AddCredentialsController.$inject = [
    'resolvedModels',
    '$state',
    '$scope',
    'CredentialsStrings',
    'ComponentsStrings',
    'ConfigService',
    'ngToast',
    'Wait',
    '$filter',
    'CredentialTypeModel',
];

export default AddCredentialsController;
