function AddCredentialsController (credentialType) {
    let vm = this || {};

    vm.name = {
        state: {
            required: true
        },
        label: {
            text: 'Name',
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
        state: {
            required: true,
        },
        label: {
            text: 'Type',
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
