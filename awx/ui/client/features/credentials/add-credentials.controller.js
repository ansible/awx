function AddCredentialsController (models, $state, strings) {
    let vm = this || {};

    let me = models.me;
    let credential = models.credential;
    let credentialType = models.credentialType;
    let organization = models.organization;

    vm.mode = 'add';
    vm.strings = strings.credentials;

    vm.panelTitle = vm.strings[vm.mode].PANEL_TITLE;

    vm.tab = {
        details: { _active: true },
        permissions:{ _disabled: true }
    };

    vm.form = credential.createFormSchema('post', {
        omit: ['user', 'team', 'inputs']
    });

    vm.form.organization._resource = 'organization';
    vm.form.organization._route = 'credentials.add.organization';
    vm.form.organization._model = organization;
    vm.form.organization._placeholder = vm.strings.inputs.ORGANIZATION_PLACEHOLDER;
    
    vm.form.credential_type._resource = 'credential_type';
    vm.form.credential_type._route = 'credentials.add.credentialType';
    vm.form.credential_type._model = credentialType;
    vm.form.credential_type._placeholder = vm.strings.inputs.CREDENTIAL_TYPE_PLACEHOLDER;

    vm.form.inputs = {
        _get: id => {
            let type = credentialType.getById(id);

            return credentialType.mergeInputProperties(type);
        },
        _source: vm.form.credential_type,
        _reference: 'vm.form.inputs',
        _key: 'inputs'
    };

    vm.form.save = data => {
        data.user = me.getSelf().id;
                
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
