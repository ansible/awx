function EditCredentialsController (models, $state) {
    let vm = this || {};

    let me = models.me;
    let credential = models.credential;
    let credentialType = models.credentialType;
    let credentialOptions = models.credentialOptions;

    vm.form = credentialOptions.createFormSchema('put', {
        omit: ['user', 'team', 'inputs'],
        models
    });

    vm.form.credential_type._data = credentialType.get('results');
    vm.form.credential_type._placeholder = 'SELECT A TYPE';
    vm.form.credential_type._format = 'grouped-object';
    vm.form.credential_type._display = 'name';
    vm.form.credential_type._key = 'id';
    vm.form.credential_type._exp = 'type as type.name group by type.kind for type in state._data';

    vm.form.inputs = {
        _get: credentialType.mergeInputProperties,
        _source: vm.form.credential_type,
        _reference: 'vm.form.inputs',
        _key: 'inputs'
    };

    vm.form.save = data => {
        data.user = me.get('results[0].id');
                
        return credential.request('post', data);
    };

    vm.form.onSaveSuccess = res => {
        $state.go('credentials.edit', { credential: res.data });
    };
}

EditCredentialsController.$inject = [
    'resolvedModels',
    '$state'
];

export default EditCredentialsController;
