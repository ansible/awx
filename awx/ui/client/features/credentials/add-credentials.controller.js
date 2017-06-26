const DEFAULT_ORGANIZATION_PLACEHOLDER = 'SELECT AN ORGANIZATION';

function AddCredentialsController (models, $state) {
    let vm = this || {};

    let me = models.me;
    let credential = models.credential;
    let credentialType = models.credentialType;

    vm.panelTitle = 'NEW CREDENTIAL';

    vm.tab = {
        details: {  
            _active: true
        },
        permissions:{
            _disabled: true
        }
    };

    vm.form = credential.createFormSchema('post', {
        omit: ['user', 'team', 'inputs']
    });

    vm.form.organization._resource = 'organization';
    vm.form.organization._route = 'credentials.add.organization';

    vm.form.credential_type._resource = 'credential_type';
    vm.form.credential_type._route = 'credentials.add.credentialType';

    vm.form.inputs = {
        _get: id => {
            let type = credentialType.getById(id);

            return credentialType.mergeInputProperties(type);
        },
        _source: vm.form.credential_type,
        _reference: 'vm.form.inputs',
        _key: 'inputs'
    };

    vm.form.save = data => {
        data.user = me.getSelf().id;
                
        return credential.request('post', data);
    };

    vm.form.onSaveSuccess = res => {
        $state.go('credentials.edit', { credential_id: res.data.id }, { reload: true });
    };
}

AddCredentialsController.$inject = [
    'resolvedModels',
    '$state'
];

export default AddCredentialsController;
