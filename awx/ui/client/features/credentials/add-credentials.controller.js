function AddCredentialsController (models, $state) {
    let vm = this || {};

    let credential = models.credential;
    let credentialType = models.credentialType;

    vm.form = credential.createFormSchema('post', {
        omit: ['user', 'team', 'inputs']
    });

    vm.form.credential_type._data = credentialType.getResults();
    vm.form.credential_type._placeholder = 'Select A Type';
    vm.form.credential_type._display = 'name';
    vm.form.credential_type._key = 'id';
    vm.form.credential_type._exp = 'type as type.name group by type.kind for type in state._data';

    vm.form.inputs = {
        _get: credentialType.mergeInputProperties,
        _source: vm.form.credential_type,
        _reference: 'vm.form.inputs',
        _key: 'inputs'
    };

    vm.form.save = credential.post;
}

AddCredentialsController.$inject = [
    'resolvedModels',
    '$state'
];

export default AddCredentialsController;
