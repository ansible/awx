function AddCredentialsController (credentialType) {
    let vm = this || {};

    vm.name = {
        label: {
            text: 'Name',
            required: true,
            popover: {}
        }
    };

    vm.description = {
        label: {
            text: 'Description'
        }
    };

    vm.heading = {
        text: 'Create Credentials'
    };

    vm.kind = {
        label: {
            text: 'Type',
            required: true,
            popover: {}
        },
        placeholder: 'Select a Type',
        text: 'kind',
        value: 'id',
        data: credentialType.categorizeByKind()
    };
}

AddCredentialsController.$inject = [
    'credentialType'
];

export default AddCredentialsController;
