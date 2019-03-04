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
    GetBasePath,
    Rest,
) {
    const vm = this || {};

    const { me, credential, credentialType, organization } = models;
    const isExternal = credentialType.get('kind') === 'external';

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

    const gceFileInputSchema = {
        id: 'gce_service_account_key',
        type: 'file',
        label: strings.get('inputs.GCE_FILE_INPUT_LABEL'),
        help_text: strings.get('inputs.GCE_FILE_INPUT_HELP_TEXT'),
    };

    let gceFileInputPreEditValues;

    vm.form.inputs = {
        _get: ({ getSubmitData }) => {
            const apiConfig = ConfigService.get();

            credentialType.mergeInputProperties();
            const fields = credential.assignInputGroupValues(apiConfig, credentialType);

            if (credentialType.get('name') === 'Google Compute Engine') {
                fields.splice(2, 0, gceFileInputSchema);
                $scope.$watch(`vm.form.${gceFileInputSchema.id}._value`, vm.gceOnFileInputChanged);
            }

            vm.getSubmitData = getSubmitData;
            vm.isTestable = credentialType.get('kind') === 'external';
            vm.inputSources.items = [];

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

    vm.externalTest = {
        form: {
            inputs: {
                _get: () => vm.externalTest.metadataInputs,
                _reference: 'vm.form.inputs',
                _key: 'inputs',
                _source: { _value: {} },
            },
        },
        metadataInputs: null,
    };
    vm.inputSources = {
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
        form: {
            inputs: {
                _get: () => vm.inputSources.metadataInputs,
                _reference: 'vm.form.inputs',
                _key: 'inputs',
                _source: { _value: {} },
            },
        },
        field: null,
        credentialTypeId: null,
        credentialTypeName: null,
        credentialId: null,
        credentialName: null,
        metadataInputs: null,
        initialItems: credential.get('related.input_sources.results'),
        items: credential.get('related.input_sources.results'),
    };

    vm.onInputSourceClear = (field) => {
        vm.form[field].tagMode = true;
        vm.form[field].asTag = false;
        vm.form[field]._value = '';
        vm.inputSources.items = vm.inputSources.items
            .filter(({ input_field_name }) => input_field_name !== field);
    };

    function setInputSourceTab (name) {
        const metaIsActive = name === 'metadata';
        vm.inputSources.tabs.credential._active = !metaIsActive;
        vm.inputSources.tabs.credential._disabled = false;
        vm.inputSources.tabs.metadata._active = metaIsActive;
        vm.inputSources.tabs.metadata._disabled = false;
    }

    function unsetInputSourceTabs () {
        vm.inputSources.tabs.credential._active = false;
        vm.inputSources.tabs.credential._disabled = false;
        vm.inputSources.tabs.metadata._active = false;
        vm.inputSources.tabs.metadata._disabled = false;
    }

    vm.onInputSourceOpen = (field) => {
        const sourceItem = vm.inputSources.items
            .find(({ input_field_name }) => input_field_name === field);
        if (sourceItem) {
            const { source_credential, summary_fields } = sourceItem;
            const { source_credential: { credential_type_id, name } } = summary_fields;
            vm.inputSources.credentialId = source_credential;
            vm.inputSources.credentialName = name;
            vm.inputSources.credentialTypeId = credential_type_id;
            vm.inputSources._value = credential_type_id;
        }
        setInputSourceTab('credential');
        vm.inputSources.field = field;
    };

    vm.onInputSourceClose = () => {
        vm.inputSources.field = null;
        vm.inputSources.credentialId = null;
        vm.inputSources.credentialName = null;
        vm.inputSources.metadataInputs = null;
        unsetInputSourceTabs();
    };

    /**
     * Extract the current set of input values from the metadata form and reshape them to a
     * metadata object that can be sent to the api later or reloaded when re-opening the form.
     */
    function getMetadataFormSubmitData ({ inputs }) {
        const metadata = Object.assign({}, ...inputs._group
            .filter(({ _value }) => _value !== undefined)
            .map(({ id, _value }) => ({ [id]: _value })));
        return metadata;
    }

    vm.onInputSourceNext = () => {
        const { field, credentialId, credentialTypeId } = vm.inputSources;
        Wait('start');
        new CredentialType('get', credentialTypeId)
            .then(model => {
                model.mergeInputProperties('metadata');
                vm.inputSources.metadataInputs = model.get('inputs.metadata');
                vm.inputSources.credentialTypeName = model.get('name');
                const [metavals] = vm.inputSources.items
                    .filter(({ input_field_name }) => input_field_name === field)
                    .filter(({ source_credential }) => source_credential === credentialId)
                    .map(({ metadata }) => metadata);
                Object.keys(metavals || {}).forEach(key => {
                    const obj = vm.inputSources.metadataInputs.find(o => o.id === key);
                    if (obj) obj._value = metavals[key];
                });
                setInputSourceTab('metadata');
            })
            .finally(() => Wait('stop'));
    };

    vm.onInputSourceSelect = () => {
        const { field, credentialId, credentialName, credentialTypeId } = vm.inputSources;
        const metadata = getMetadataFormSubmitData(vm.inputSources.form);
        vm.inputSources.items = vm.inputSources.items
            .filter(({ input_field_name }) => input_field_name !== field)
            .concat([{
                metadata,
                input_field_name: field,
                source_credential: credentialId,
                target_credential: credential.get('id'),
                summary_fields: {
                    source_credential: {
                        name: credentialName,
                        credential_type_id: credentialTypeId
                    }
                },
            }]);
        vm.inputSources.field = null;
        vm.inputSources.metadataInputs = null;
        unsetInputSourceTabs();
        vm.form[field]._value = credentialName;
        vm.form[field].asTag = true;
    };

    vm.onInputSourceTabSelect = (name) => {
        if (name === 'metadata') {
            vm.onInputSourceNext();
        } else {
            setInputSourceTab('credential');
        }
    };

    vm.onInputSourceRowClick = ({ id, credential_type, name }) => {
        vm.inputSources.credentialId = id;
        vm.inputSources.credentialName = name;
        vm.inputSources.credentialTypeId = credential_type;
        vm.inputSources._value = credential_type;
    };

    vm.onInputSourceTest = () => {
        const metadata = getMetadataFormSubmitData(vm.inputSources.form);
        const name = $filter('sanitize')(vm.inputSources.credentialTypeName);
        const endpoint = `${vm.inputSources.credentialId}/test/`;
        return runTest({ name, model: credential, endpoint, data: { metadata } });
    };

    function onExternalTestOpen () {
        credentialType.mergeInputProperties('metadata');
        vm.externalTest.metadataInputs = credentialType.get('inputs.metadata');
    }
    vm.form.secondary = onExternalTestOpen;

    vm.onExternalTestClose = () => {
        vm.externalTest.metadataInputs = null;
    };

    vm.onExternalTest = () => {
        const name = $filter('sanitize')(credentialType.get('name'));
        const { inputs } = vm.getSubmitData();
        const metadata = getMetadataFormSubmitData(vm.externalTest.form);

        let model;
        if (credential.get('credential_type') !== credentialType.get('id')) {
            model = credentialType;
        } else {
            model = credential;
        }

        const endpoint = `${model.get('id')}/test/`;
        return runTest({ name, model, endpoint, data: { inputs, metadata } });
    };

    vm.filterInputSourceCredentialResults = (data) => {
        if (isExternal) {
            data.results = data.results.filter(({ id }) => id !== credential.get('id'));
        }
        return data;
    };

    function runTest ({ name, model, endpoint, data: { inputs, metadata } }) {
        return model.http.post({ url: endpoint, data: { inputs, metadata }, replace: false })
            .then(() => {
                const icon = 'fa-check-circle';
                const msg = strings.get('edit.TEST_PASSED');
                const content = buildTestNotificationContent({ name, icon, msg });
                ngToast.success({
                    content,
                    dismissButton: false,
                    dismissOnTimeout: true
                });
            })
            .catch(({ data }) => {
                const icon = 'fa-exclamation-triangle';
                const msg = data.inputs || strings.get('edit.TEST_FAILED');
                const content = buildTestNotificationContent({ name, icon, msg });
                ngToast.danger({
                    content,
                    dismissButton: false,
                    dismissOnTimeout: true
                });
            });
    }

    function buildTestNotificationContent ({ name, msg, icon }) {
        const sanitize = $filter('sanitize');
        const content = `<div class="Toast-wrapper">
            <div class="Toast-icon">
                <i class="fa ${icon} Toast-successIcon"></i>
            </div>
            <div>
                <b>${sanitize(name)}:</b> ${sanitize(msg)}
            </div>
        </div>`;
        return content;
    }

    function createInputSource (data) {
        Rest.setUrl(GetBasePath('credential_input_sources'));
        return Rest.post(data);
    }

    vm.form.save = data => {
        data.user = me.get('id');

        if (_.get(data.inputs, gceFileInputSchema.id)) {
            delete data.inputs[gceFileInputSchema.id];
        }

        const updatedLinkedFieldNames = vm.inputSources.items
            .map(({ input_field_name }) => input_field_name);
        const sourcesToAssociate = [...vm.inputSources.items];

        // remove inputs with empty string values
        let filteredInputs = _.omit(data.inputs, (value) => value === '');
        // remove inputs that are to be linked to an external credential
        filteredInputs = _.omit(filteredInputs, updatedLinkedFieldNames);
        data.inputs = filteredInputs;

        return credential.request('post', { data })
            .then(() => {
                sourcesToAssociate.forEach(obj => { obj.target_credential = credential.get('id'); });
                return Promise.all(sourcesToAssociate.map(createInputSource));
            });
    };

    vm.form.onSaveSuccess = () => {
        $state.go('credentials.edit', { credential_id: credential.get('id') }, { reload: true });
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
    'GetBasePath',
    'Rest',
];

export default AddCredentialsController;
