/*************************************************
 * Copyright (c) 2018 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
function MultiCredentialModal(
    templateUrl,
    generateList,
    $compile,
    CreateSelect2,
    i18n,
    CredentialList
) {
    const templatePath = 'templates/job_templates/multi-credential/multi-credential-modal';
    const emptyListText = i18n._('No Credentials Matching This Type Have Been Created');

    const list = _.cloneDeep(CredentialList);
    const vaultList = _.cloneDeep(CredentialList);

    list.emptyListText = emptyListText;

    vaultList.emptyListText = emptyListText;
    vaultList.fields.name.modalColumnClass = 'col-md-6';
    vaultList.fields.info = {
        label: i18n._('Vault ID'),
        ngBind: 'credential.inputs.vault_id',
        key: false,
        nosort: true,
        modalColumnClass: 'col-md-6',
        infoHeaderClass: '',
        dataPlacement: 'top',
    };

    const listHtml = generateList.build({ mode: 'lookup', input_type: 'radio', list });
    const vaultHtml = generateList.build({ mode: 'lookup', input_type: 'checkbox', list: vaultList });

    return {
        templateUrl: templateUrl(templatePath),
        restrict: 'E',
        controllerAs: 'vm',
        require: ['multiCredentialModal'],
        scope: {
            credentialTypes: '=',
            selectedCredentials: '=',
        },
        link: (scope, element, attrs, controllers) => {
            const compiledList = $compile(listHtml)(scope);
            const compiledVaultList = $compile(vaultHtml)(scope);

            const modalBodyElement = $('#multi-credential-modal-body');
            const modalElement = $('#multi-credential-modal');

            scope.showModal = () => modalElement.modal('show');
            scope.hideModal = () => modalElement.modal('hide');

            scope.createList = () => modalBodyElement.append(compiledList);
            scope.createVaultList = () => modalBodyElement.append(compiledVaultList);
            scope.destroyList = () => modalBodyElement.empty();

            modalElement.on('hidden.bs.modal', () => {
                modalElement.off('hidden.bs.modal');
                $(element).remove();
            });

            CreateSelect2({
                placeholder: i18n._('Select a credential'),
                element: '#multi-credential-kind-select',
                multiple: false,
            });

            scope.list = list;
            controllers[0].init(scope);
        },
        controller: ['GetBasePath', 'QuerySet', 'MultiCredentialService',
            multiCredentialModalController],
    };
}

function multiCredentialModalController(GetBasePath, qs, MultiCredentialService) {
    const vm = this;
    const { createTag, isReadOnly } = MultiCredentialService;

    const types = {};
    const unwatch = [];

    let scope;

    vm.init = _scope_ => {
        scope = _scope_;
        scope.modalSelectedCredentials = _.cloneDeep(scope.selectedCredentials);

        scope.credentialTypes.forEach(({ name, id }) => types[name] = id);

        scope.toggle_row = vm.toggle_row;
        scope.toggle_credential = vm.toggle_credential;

        scope.credential_default_params = { order_by: 'name', page_size: 5 };
        scope.credential_queryset = { order_by: 'name', page_size: 5 };
        scope.credential_dataset = { results: [], count: 0 };
        scope.credentials = scope.credential_dataset.results;

        scope.credentialType = getInitialCredentialType();
        scope.displayedCredentialTypes = scope.credentialTypes;

        const watchType = scope.$watch('credentialType', (newValue, oldValue) => {
            if (newValue !== oldValue) {
                fetchCredentials(parseInt(newValue));
            }
        });
        scope.$watchCollection('modalSelectedCredentials', updateListView);
        scope.$watchCollection('modalSelectedCredentials', updateTagView);
        scope.$watchCollection('modalSelectedCredentials', updateDisplayedCredentialTypes);
        scope.$watchCollection('credentials', updateListView);

        unwatch.push(watchType);

        fetchCredentials(parseInt(scope.credentialType))
            .then(scope.showModal);
    };

    function updateTagView () {
        scope.tags = scope.modalSelectedCredentials
            .map(c => createTag(c, scope.credentialTypes));
    }

    function updateListView () {
        scope.credentials.forEach(credential => {
            const index = scope.modalSelectedCredentials
                .map(({ id }) => id)
                .indexOf(credential.id);

            if (index > -1) {
                credential.checked = 1;
            } else {
                credential.checked = 0;
            }
        });
    }

    function updateDisplayedCredentialTypes() {
        const displayedCredentialTypes = _.cloneDeep(scope.credentialTypes);

        scope.modalSelectedCredentials.forEach(credential => {
            const credentialTypeId = credential.credential_type || credential.credential_type_id;

            if(isReadOnly(credential) && credentialTypeId !== types.Vault) {
                const index = displayedCredentialTypes
                    .map(t => t.id).indexOf(credentialTypeId);

                if (index > -1) {
                    displayedCredentialTypes.splice(index, 1);
                }
            }
        });

        scope.displayedCredentialTypes = displayedCredentialTypes;
    }

    function getInitialCredentialType () {
        const selectedMachineCredential = scope.modalSelectedCredentials
            .find(c => c.id === types.Machine);

        if (selectedMachineCredential && isReadOnly(selectedMachineCredential)) {
            return `${types.Vault}`;
        }

        return `${types.Machine}`;
    }

    function fetchCredentials (credentialType) {
        const endpoint = GetBasePath('credentials');

        scope.credential_queryset.page = 1;
        scope.credential_default_params.credential_type = credentialType;
        scope.credential_queryset.credential_type = credentialType;

        return qs.search(endpoint, scope.credential_default_params)
            .then(({ data }) => {
                const results = data.results.filter(c => !isReadOnly(c));
                const readOnlyCount = data.results.length - results.length;

                data.results = results;
                data.count = data.count - readOnlyCount;

                scope.credential_dataset = data;
                scope.credentials = data.results;

                scope.destroyList();

                if (credentialType === types.Vault) {
                    scope.createVaultList();
                } else {
                    scope.createList();
                }
            });
    }

    vm.revertSelectedCredentials = () => {
        scope.modalSelectedCredentials = _.cloneDeep(scope.selectedCredentials);
    };

    vm.removeCredential = id => {
        const index = scope.modalSelectedCredentials.map(c => c.id).indexOf(id);
        const isSelected = index > -1;

        if (isSelected) {
            scope.modalSelectedCredentials.splice(index, 1);
            return;
        }
    };

    vm.toggle_credential = id => {
        // This is called only when a checkbox input is clicked directly. Clicks anywhere else on
        // the row or direct radio button clicks invoke the toggle_row handler instead with a
        // different set of arguments. We normalize those arguments here and pass them through to
        // the other function so that the behavior is consistent.
        const credential = scope.credentials.find(c => c.id === id);
        scope.toggle_row(credential);
    };

    vm.toggle_row = credential => {
        const index = scope.modalSelectedCredentials.map(c => c.id).indexOf(credential.id);
        const isSelected = index > -1;

        if (isSelected) {
            scope.modalSelectedCredentials.splice(index, 1);
            return;
        }

        const credentialTypeId = credential.credential_type || credential.credential_type_id;

        if (credentialTypeId === types.Vault) {
            const vaultId = _.get(credential, 'inputs.vault_id');

            scope.modalSelectedCredentials = scope.modalSelectedCredentials
                .filter(c => (c.credential_type !== types.Vault) || (c.inputs.vault_id !== vaultId))
                .concat([credential]);
        } else {
            scope.modalSelectedCredentials = scope.modalSelectedCredentials
                .filter(({ credential_type }) => credential_type !== credentialTypeId)
                .concat([credential]);
        }
    };

    vm.cancelForm = () => {
        unwatch.forEach(cb => cb());
        scope.hideModal();
    };

    vm.saveForm = () => {
        scope.selectedCredentials = _.cloneDeep(scope.modalSelectedCredentials);
        unwatch.forEach(cb => cb());
        scope.hideModal();
    };
}

MultiCredentialModal.$inject = [
    'templateUrl',
    'generateList',
    '$compile',
    'CreateSelect2',
    'i18n',
    'CredentialList',
];

export default MultiCredentialModal;
