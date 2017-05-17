function AddCredentialsController (models) {
    let vm = this || {};

    let credential = models.credential;
    let credentialType = models.credentialType;
    
    vm.name = credential.getPostOptions('name');
    vm.description = credential.getPostOptions('description');

    vm.kind = Object.assign({
        data: credentialType.categorizeByKind(),
        placeholder: 'Select a Type'
    }, credential.getPostOptions('credential_type'));

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
