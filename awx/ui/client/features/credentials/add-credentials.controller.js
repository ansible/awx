function AddCredentialsController (models, $state, strings) {
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

    vm.form.disabled = !credential.isCreatable();

    vm.form.organization._resource = 'organization';
    vm.form.organization._route = 'credentials.add.organization';
    vm.form.organization._model = organization;
    vm.form.organization._placeholder = strings.get('inputs.ORGANIZATION_PLACEHOLDER');

    vm.form.credential_type._resource = 'credential_type';
    vm.form.credential_type._route = 'credentials.add.credentialType';
    vm.form.credential_type._model = credentialType;
    vm.form.credential_type._placeholder = strings.get('inputs.CREDENTIAL_TYPE_PLACEHOLDER');

    vm.form.inputs = {
        _get: () => {
            credentialType.mergeInputProperties();

            return credentialType.get('inputs.fields');
        },
        _source: vm.form.credential_type,
        _reference: 'vm.form.inputs',
        _key: 'inputs'
    };

    vm.form.save = data => {
        data.user = me.get('id');

        return credential.request('post', data);
    };

    vm.form.onSaveSuccess = res => {
        $state.go('credentials.edit', { credential_id: res.data.id }, { reload: true });
    };
}

AddCredentialsController.$inject = [
    'resolvedModels',
    '$state',
    'CredentialsStrings'
];

export default AddCredentialsController;
