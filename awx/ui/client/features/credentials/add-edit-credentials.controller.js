/* eslint camelcase: 0 */
/* eslint arrow-body-style: 0 */
function AddEditCredentialsController (
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
    const {
        me,
        credential,
        credentialType,
        organization,
        isOrgEditableByUser,
        sourceCredentials,
    } = models;

    const omit = ['user', 'team', 'inputs'];
    const isEditable = credential.isEditable();
    const isExternal = credentialType.get('kind') === 'external';
    const mode = $state.current.name.startsWith('credentials.add') ? 'add' : 'edit';

    vm.isEditable = credential.get('summary_fields.user_capabilities.edit');
    vm.mode = mode;
    vm.strings = strings;

    if (mode === 'edit') {
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

        if (isEditable) {
            vm.form = credential.createFormSchema('put', { omit });
        } else {
            vm.form = credential.createFormSchema({ omit });
            vm.form.disabled = !isEditable;
        }
        vm.form.disabled = !vm.isEditable;

        vm.form._organization._disabled = !isOrgEditableByUser;
        // Only exists for permissions compatibility
        $scope.credential_obj = credential.get();

        // Custom credentials can have input fields named 'name', 'organization',
        // 'description', etc. Underscore these variables to make collisions
        // less likely to occur.
        vm.form._organization._resource = 'organization';
        vm.form._organization._model = organization;
        vm.form._organization._route = 'credentials.edit.organization';
        vm.form._organization._value = credential.get('summary_fields.organization.id');
        vm.form._organization._displayValue = credential.get('summary_fields.organization.name');
        vm.form._organization._placeholder = strings.get('inputs.ORGANIZATION_PLACEHOLDER');

        vm.form.credential_type._resource = 'credential_type';
        vm.form.credential_type._model = credentialType;
        vm.form.credential_type._route = 'credentials.edit.credentialType';
        vm.form.credential_type._placeholder = strings.get('inputs.CREDENTIAL_TYPE_PLACEHOLDER');
        vm.form.credential_type._value = credentialType.get('id');
        vm.form.credential_type._displayValue = credentialType.get('name');
        vm.isTestable = (isEditable && credentialType.get('kind') === 'external');

        if (credential.get('related.input_sources.results').length > 0) {
            vm.form.credential_type._disabled = true;
        }

        $scope.$watch('$state.current.name', (value) => {
            if (/credentials.edit($|\.organization$|\.credentialType$)/.test(value)) {
                vm.tab.details._active = true;
                vm.tab.permissions._active = false;
            } else {
                vm.tab.permissions._active = true;
                vm.tab.details._active = false;
            }
        });
    } else if (mode === 'add') {
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

        vm.form._organization._resource = 'organization';
        vm.form._organization._route = 'credentials.add.organization';
        vm.form._organization._model = organization;
        vm.form._organization._placeholder = strings.get('inputs.ORGANIZATION_PLACEHOLDER');

        vm.form.credential_type._resource = 'credential_type';
        vm.form.credential_type._route = 'credentials.add.credentialType';
        vm.form.credential_type._model = credentialType;
        vm.form.credential_type._placeholder = strings.get('inputs.CREDENTIAL_TYPE_PLACEHOLDER');
        vm.isTestable = credentialType.get('kind') === 'external';
    }

    $scope.$watch('organization', () => {
        if ($scope.organization) {
            vm.form._organization._idFromModal = $scope.organization;
        }
    });

    $scope.$watch('credential_type', () => {
        if ($scope.credential_type) {
            vm.form.credential_type._idFromModal = $scope.credential_type;
        }
    });

    const gceFileInputSchema = {
        id: 'gce_service_account_key',
        type: 'file',
        label: strings.get('inputs.GCE_FILE_INPUT_LABEL'),
        help_text: strings.get('inputs.GCE_FILE_INPUT_HELP_TEXT'),
    };

    let gceFileInputPreEditValues;

    vm.form.inputs = {
        _get ({ getSubmitData, check }) {
            const apiConfig = ConfigService.get();

            credentialType.mergeInputProperties();
            const fields = credential.assignInputGroupValues(
                apiConfig,
                credentialType,
                sourceCredentials
            );

            if (credentialType.get('name') === 'Google Compute Engine') {
                fields.splice(2, 0, gceFileInputSchema);
                $scope.$watch(`vm.form.${gceFileInputSchema.id}._value`, gceOnFileInputChanged);
                if (mode === 'edit') {
                    $scope.$watch('vm.form.ssh_key_data._isBeingReplaced', gceOnReplaceKeyChanged);
                }
            }

            vm.inputSources.initialItems = credential.get('related.input_sources.results');
            vm.inputSources.items = [];
            vm.inputSources.changedInputFields = [];
            if (credential.get('credential_type') === credentialType.get('id')) {
                vm.inputSources.items = credential.get('related.input_sources.results');
            }

            if (mode === 'add') {
                vm.isTestable = (models.me.get('is_superuser') && credentialType.get('kind') === 'external');
            } else {
                vm.isTestable = (isEditable && credentialType.get('kind') === 'external');
            }

            vm.getSubmitData = getSubmitData;
            vm.checkForm = check;

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
        _key: 'inputs',
        border: true,
        title: true,
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
        changedInputFields: [],
        initialItems: credential.get('related.input_sources.results'),
        items: credential.get('related.input_sources.results'),
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

    vm.onInputSourceClear = (field) => {
        vm.form[field].tagMode = true;
        vm.form[field].asTag = false;
        vm.form[field]._value = '';
        vm.form[field]._tagValue = '';
        vm.form[field]._isValid = true;
        vm.form[field]._rejected = false;
        vm.inputSources.items = vm.inputSources.items
            .filter(({ input_field_name }) => input_field_name !== field);
        vm.inputSources.changedInputFields.push(field);
    };

    vm.onInputSourceOpen = (field) => {
        // We get here when the input source lookup modal for a field is opened. If source
        // credential and metadata values for this field already exist in the initial API data
        // or from it being set during a prior visit to the lookup, we initialize the lookup with
        // these values here before opening it.
        const sourceItem = vm.inputSources.items
            .find(({ input_field_name }) => input_field_name === field);
        if (sourceItem) {
            const { source_credential, summary_fields } = sourceItem;
            const { source_credential: { credential_type_id, name } } = summary_fields;
            vm.inputSources.credentialId = source_credential;
            vm.inputSources.credentialName = name;
            vm.inputSources.credentialTypeId = credential_type_id;
            vm.inputSources._value = credential_type_id;
        } else {
            vm.inputSources.credentialId = null;
            vm.inputSources.credentialName = null;
            vm.inputSources.credentialTypeId = null;
            vm.inputSources._value = null;
        }

        setInputSourceTab('credential');
        vm.inputSources.field = field;
    };

    vm.onInputSourceClose = () => {
        // We get here if the lookup was closed or canceled so we clear the state for the lookup
        // and metadata form without storing any changes.
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
        return inputs._group.reduce((metadata, { id, _value }) => {
            if (_value !== undefined) {
                metadata[id] = _value;
            }
            return metadata;
        }, {});
    }

    vm.onInputSourceNext = () => {
        const { field, credentialId, credentialTypeId } = vm.inputSources;
        Wait('start');
        new CredentialType('get', credentialTypeId)
            .then(model => {
                model.mergeInputProperties('metadata');
                vm.inputSources.metadataInputs = model.get('inputs.metadata');
                vm.inputSources.credentialTypeName = model.get('name');
                // Pre-populate the input values for the metadata form if state for this specific
                // field_name->source_credential link already exists. This occurs one of two ways:
                //
                // 1. This field->source_credential link already exists in the API and so we're
                //    showing the current state as it exists on the backend.
                // 2. The metadata form for this specific field->source_credential combination was
                //    set during a prior visit to this lookup and so we're reflecting the most
                //    recent set of (unsaved) metadata values provided by the user for this field.
                //
                // Note: Prior state for a given credential input field is only set for one source
                // credential at a time. Linking a field to a source credential will remove all
                // other prior input state for that field.
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
        // Remove any input source objects already stored for this field then store the metadata
        // and currently selected source credential as a credential input source object that
        // can be sent to the api later or reloaded into the form if it is reopened.
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
        // Record that this field was changed
        vm.inputSources.changedInputFields.push(field);
        // Now that we've extracted and stored the selected source credential and metadata values
        // for this field, we clear the state for the source credential lookup and metadata form.
        vm.inputSources.field = null;
        vm.inputSources.metadataInputs = null;
        unsetInputSourceTabs();
        // We've linked this field to a credential, so display value as a credential tag
        vm.form[field]._value = '';
        vm.form[field]._tagValue = credentialName;
        vm.form[field]._isValid = true;
        vm.form[field].asTag = true;
        vm.checkForm();
    };

    vm.onInputSourceTabSelect = (name) => {
        if (name === 'metadata') {
            // Clicking on the metadata tab should have identical behavior to clicking the 'next'
            // button, so we pass-through to the same handler here.
            vm.onInputSourceNext();
        } else {
            setInputSourceTab('credential');
        }
    };

    vm.onInputSourceItemSelect = ({ id, credential_type, name }) => {
        vm.inputSources.credentialId = id;
        vm.inputSources.credentialName = name;
        vm.inputSources.credentialTypeId = credential_type;
        vm.inputSources._value = credential_type;
    };

    vm.onInputSourceTest = () => {
        // We get here if the test button on the metadata form for the field of a non-external
        // credential was used. All input values for the external credential are already stored
        // on the backend, so we are only testing how it works with a set of metadata before
        // linking it.
        const metadata = getMetadataFormSubmitData(vm.inputSources.form);
        const name = $filter('sanitize')(vm.inputSources.credentialTypeName);
        const endpoint = `${vm.inputSources.credentialId}/test/`;
        return runTest({ name, model: credential, endpoint, data: { metadata } });
    };

    function onExternalTestOpen () {
        // We get here if test button on the top-level form for an external credential type was
        // used. We load the metadata schema for this particular external credential type and
        // use it to generate and open a form for submitting test values.
        credentialType.mergeInputProperties('metadata');
        vm.externalTest.metadataInputs = credentialType.get('inputs.metadata');
    }
    vm.form.secondary = onExternalTestOpen;

    vm.onExternalTestClose = () => {
        // We get here if the metadata test form for an external credential type was canceled or
        // closed so we clear the form state and close without submitting any data to the test api,
        vm.externalTest.metadataInputs = null;
    };

    vm.onExternalTest = () => {
        const name = $filter('sanitize')(credentialType.get('name'));
        const { inputs } = vm.getSubmitData();
        const metadata = getMetadataFormSubmitData(vm.externalTest.form);
        // We get here if the test button on the top-level form for an external credential type was
        // used. We need to see if the currently selected credential type is the one loaded from
        // the api when we initialized the view or if its type was changed on the form and hasn't
        // been saved. If the credential type hasn't been changed, it means some of the input
        // values for the credential may be stored in the backend and not in the form, so we need
        // to use the test endpoint for the credential. If the credential type has been changed,
        // the user must provide a complete set of input values for the credential to save their
        // changes, so we use the generic test endpoint for the credental type as if we were
        // testing a completely new and unsaved credential.
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
        // If an external credential is changed to have a non-external `credential_type` while
        // editing, we avoid showing a self-reference in the list of selectable external
        // credentials for input fields by filtering it out here.
        if (isExternal) {
            data.results = data.results.filter(({ id }) => id !== credential.get('id'));
        }

        // only show credentials we can use
        data.results = data.results
            .filter(({ summary_fields }) => summary_fields.user_capabilities.use);

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

    function deleteInputSource ({ id }) {
        Rest.setUrl(`${GetBasePath('credential_input_sources')}${id}/`);
        return Rest.destroy();
    }

    function createInputSource (data) {
        Rest.setUrl(GetBasePath('credential_input_sources'));
        return Rest.post(data);
    }

    function create (data) {
        // can send only one of org, user, team
        if (!data.organization && !data.team) {
            data.user = me.get('id');
        }

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
    }

    /**
     * If a credential's `credential_type` is changed while editing, the inputs associated with
     * the old type need to be cleared before saving the inputs associated with the new type.
     * Otherwise inputs are merged together making the request invalid.
     */
    function update (data) {
        // can send only one of org, user, team
        if (!data.organization && !data.team) {
            data.user = me.get('id');
        }

        credential.unset('inputs');

        if (_.get(data.inputs, gceFileInputSchema.id)) {
            delete data.inputs[gceFileInputSchema.id];
        }

        const initialLinkedFieldNames = vm.inputSources.initialItems
            .map(({ input_field_name }) => input_field_name);
        const updatedLinkedFieldNames = vm.inputSources.items
            .map(({ input_field_name }) => input_field_name);

        const fieldsToDisassociate = initialLinkedFieldNames
            .filter(name => !updatedLinkedFieldNames.includes(name))
            .concat(updatedLinkedFieldNames)
            .filter(name => vm.inputSources.changedInputFields.includes(name));
        const fieldsToAssociate = updatedLinkedFieldNames
            .filter(name => vm.inputSources.changedInputFields.includes(name));

        const sourcesToDisassociate = fieldsToDisassociate
            .map(name => vm.inputSources.initialItems
                .find(({ input_field_name }) => input_field_name === name))
            .filter(source => source !== undefined);
        const sourcesToAssociate = fieldsToAssociate
            .map(name => vm.inputSources.items
                .find(({ input_field_name }) => input_field_name === name))
            .filter(source => source !== undefined);

        // remove inputs with empty string values
        let filteredInputs = _.omit(data.inputs, (value) => value === '');
        // remove inputs that are to be linked to an external credential
        filteredInputs = _.omit(filteredInputs, updatedLinkedFieldNames);
        data.inputs = filteredInputs;

        return credential.request('put', { data })
            .then(() => Promise.all(sourcesToDisassociate.map(deleteInputSource)))
            .then(() => Promise.all(sourcesToAssociate.map(createInputSource)));
    }

    vm.form.save = data => {
        if (mode === 'edit') {
            return update(data);
        }
        return create(data);
    };

    vm.form.onSaveSuccess = () => {
        $state.go('credentials.edit', { credential_id: credential.get('id') }, { reload: true });
    };

    function gceOnReplaceKeyChanged (value) {
        vm.form[gceFileInputSchema.id]._disabled = !value;
    }

    function gceOnFileInputChanged (value, oldValue) {
        if (value === oldValue) return;

        const gceFileIsLoaded = !!value;
        const gceFileInputState = vm.form[gceFileInputSchema.id];
        const { obj, error } = gceParseFileInput(value);

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

            vm.form.project.asTag = false;
            vm.form.project._value = _.get(obj, 'project_id', '');
            vm.inputSources.changedInputFields.push('project');
            vm.inputSources.items = vm.inputSources.items
                .filter(({ input_field_name }) => input_field_name !== 'project');

            vm.form.ssh_key_data.asTag = false;
            vm.form.ssh_key_data._value = _.get(obj, 'private_key', '');
            vm.inputSources.changedInputFields.push('ssh_key_data');
            vm.inputSources.items = vm.inputSources.items
                .filter(({ input_field_name }) => input_field_name !== 'ssh_key_data');

            vm.form.username.asTag = false;
            vm.form.username._value = _.get(obj, 'client_email', '');
            vm.inputSources.changedInputFields.push('username');
            vm.inputSources.items = vm.inputSources.items
                .filter(({ input_field_name }) => input_field_name !== 'username');
        } else {
            vm.form.project._value = gceFileInputPreEditValues.project;
            vm.form.ssh_key_data._value = gceFileInputPreEditValues.ssh_key_data;
            vm.form.username._value = gceFileInputPreEditValues.username;
        }
    }

    function gceParseFileInput (value) {
        let obj;
        let error;

        try {
            obj = angular.fromJson(value);
        } catch (err) {
            error = err;
        }

        return { obj, error };
    }
}

AddEditCredentialsController.$inject = [
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

export default AddEditCredentialsController;
