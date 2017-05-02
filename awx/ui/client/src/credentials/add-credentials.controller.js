function AddCredentialsController (credentialType) {
    let vm = this || {};

    vm.name = {
        label: 'Name',
        required: true
    };

    vm.description = {
        label: 'Description'
    };

    vm.kind = {
        label: 'Type',
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
