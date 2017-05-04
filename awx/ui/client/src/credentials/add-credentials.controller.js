function AddCredentialsController (credentialType) {
    let vm = this || {};

    vm.name = {
        label: 'Name',
        required: true
    };

    vm.description = {
        label: 'Description'
    };

    vm.heading = {
        text: 'Create Credentials'
    };

    vm.kind = {
        label: 'Type',
        placeholder: 'Select a Type',
        required: true,
        text: 'kind',
        value: 'id',
        data: credentialType.categorizeByKind()
    };
}

AddCredentialsController.$inject = [
    'credentialType'
];

export default AddCredentialsController;
