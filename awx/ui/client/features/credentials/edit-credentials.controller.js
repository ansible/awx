function EditCredentialsController (models, $state) {
    let vm = this || {};

    let me = models.me;
    let credential = models.credential;
    let credentialType = models.credentialType;

    vm.panelTitle = credential.get('name');

    vm.form = credential.createFormSchema('put', {
        omit: ['user', 'team', 'inputs']
    });

    vm.form.credential_type._data = credentialType.get('results');
    vm.form.credential_type._format = 'grouped-object';
    vm.form.credential_type._display = 'name';
    vm.form.credential_type._key = 'id';
    vm.form.credential_type._exp = 'type as type.name group by type.kind for type in state._data';
    vm.form.credential_type._value = credentialType.getById(credential.get('credential_type'));

    vm.form.inputs = {
        _get (type) {
            let inputs = credentialType.mergeInputProperties(type);
            
            if (type.id === credential.get('credential_type')) {
                inputs = credential.assignInputGroupValues(inputs);
            }

            return inputs;
        },
        _source: vm.form.credential_type,
        _reference: 'vm.form.inputs',
        _key: 'inputs'
    };

    vm.form.save = data => {
        data.user = me.getSelf().id;
                
        return credential.request('put', data);
    };

    vm.form.onSaveSuccess = res => {
        $state.go('credentials', { reload: true });
    };
}

EditCredentialsController.$inject = [
    'resolvedModels',
    '$state'
];

export default EditCredentialsController;
