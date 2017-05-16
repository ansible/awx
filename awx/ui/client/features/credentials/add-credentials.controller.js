function AddCredentialsController (models) {
    let vm = this || {};

    let credential = models.credential;
    let credentialType = models.credentialType;
    
    vm.heading = {
        text: 'Create Credentials'
    };

    vm.name = {
        options: credential.getPostOptions('name')
    };

    vm.description = {
        options: credential.getPostOptions('description')
    };

    vm.kind = {
        options: credential.getPostOptions('credential_type'),
        data: credentialType.categorizeByKind(),
        placeholder: 'Select a Type'
    };

    vm.dynamic = {
        getInputs: credentialType.getTypeFromName,
        source: vm.kind,
        reference: 'vm.dynamic'
    };
}

AddCredentialsController.$inject = [
    'credentialType'
];

export default AddCredentialsController;
