function AddCredentialsController (models) {
    let vm = this || {};

    let credential = models.credential;
    let credentialType = models.credentialType;

    vm.form = credential.createFormSchema('post', {
        omit: ['user', 'team', 'inputs']
    });

    vm.form.credential_type.data = credentialType.categorizeByKind();
    vm.form.credential_type.placeholder = 'Select A Type';

    vm.form.inputs = {
        get: credentialType.getTypeFromName,
        source: vm.form.credential_type,
        reference: 'vm.form.inputs',
        key: 'inputs'
    };

    vm.form.save = credential.post;
}

AddCredentialsController.$inject = [
    'resolvedModels'
];

export default AddCredentialsController;
