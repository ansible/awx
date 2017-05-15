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

    vm.dynamic = {
        update: type => {
            this.inputs = type ? type.inputs.fields : null;
        }
    };

    vm.kind = {
        options: credential.getPostOptions('credential_type'),
        data: credentialType.categorizeByKind(),
        notify: vm.dynamic.update,
        placeholder: 'Select a Type'
    };
}

AddCredentialsController.$inject = [
    'credentialType'
];

export default AddCredentialsController;
