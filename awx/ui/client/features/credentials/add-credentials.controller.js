const DEFAULT_ORGANIZATION_PLACEHOLDER = 'SELECT AN ORGANIZATION';

function AddCredentialsController (models, $state) {
    let vm = this || {};

    let me = models.me;
    let credential = models.credential;
    let credentialType = models.credentialType;
    let organization = models.organization;

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

    vm.form.organization._placeholder = DEFAULT_ORGANIZATION_PLACEHOLDER;
    vm.form.organization._data = organization.get('results');
    vm.form.organization._format = 'objects';
    vm.form.organization._exp = 'org as org.name for org in state._data';
    vm.form.organization._display = 'name';
    vm.form.organization._key = 'id';

    vm.form.credential_type._data = credentialType.get('results');
    vm.form.credential_type._placeholder = 'SELECT A TYPE';
    vm.form.credential_type._format = 'grouped-object';
    vm.form.credential_type._display = 'name';
    vm.form.credential_type._key = 'id';
    vm.form.credential_type._exp = 'type as type.name group by type.kind for type in state._data';

    vm.form.inputs = {
        _get: credentialType.mergeInputProperties,
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
