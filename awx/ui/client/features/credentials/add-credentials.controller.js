function AddCredentialsController (models, $state) {
    let vm = this || {};

    let me = models.me;
    let credential = models.credential;
    let credentialType = models.credentialType;

    vm.form = credential.createFormSchema('post', {
        omit: ['user', 'team', 'inputs']
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

    vm.form.saveSuccess = res => {
        $state.go('credentials.edit', { id: res.data.id });
    };
}

AddCredentialsController.$inject = [
    'resolvedModels',
    '$state'
];

export default AddCredentialsController;
