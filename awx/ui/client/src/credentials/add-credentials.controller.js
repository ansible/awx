function AddCredentialsController (credentialType) {
    let vm = this || {};

    vm.name = {
        label: {
            text: 'Name',
            required: true,
            popover: {
                text: 'a, b, c'
            }
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
            popover: {
                text: 'x, y, z'
            }
        },
        placeholder: 'Select a Type',
        text: 'kind',
        value: 'id',
        data: credentialType.categorizeByKind()
    };

    vm.save = {
        type: 'save'
    };

    vm.cancel = {
        type: 'cancel'
    };
}

AddCredentialsController.$inject = [
    'credentialType'
];

export default AddCredentialsController;
