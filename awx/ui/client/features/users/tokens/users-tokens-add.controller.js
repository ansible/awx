function AddTokensController (
    models, $state, strings, Rest, Alert, Wait, GetBasePath,
    $filter, ProcessErrors
) {
    const vm = this || {};
    const { application } = models;

    vm.mode = 'add';
    vm.strings = strings;
    vm.panelTitle = strings.get('add.PANEL_TITLE');

    vm.form = {};

    vm.form.application = {
        type: 'field',
        label: 'Application',
        id: 'application'
    };
    vm.form.description = {
        type: 'String',
        label: 'Description',
        id: 'description'
    };

    vm.form.application._resource = 'application';
    vm.form.application._route = 'users.edit.tokens.add.application';
    vm.form.application._model = application;
    vm.form.application._placeholder = strings.get('add.APP_PLACEHOLDER');
    vm.form.application.required = true;

    vm.form.description.required = false;

    vm.form.scope = {
        choices: [
            '',
            'read',
            'write'
        ],
        help_text: strings.get('add.SCOPE_HELP_TEXT'),
        id: 'scope',
        label: 'Scope',
        required: true,
        _component: 'at-input-select',
        _data: [
            strings.get('add.SCOPE_PLACEHOLDER'),
            strings.get('add.SCOPE_READ_LABEL'),
            strings.get('add.SCOPE_WRITE_LABEL')
        ],
        _exp: 'choice for (index, choice) in state._data',
        _format: 'array'
    };

    vm.form.save = payload => {
        Rest.setUrl(`${GetBasePath('users')}${$state.params.user_id}/authorized_tokens`);
        return Rest.post(payload)
            .then(({ data }) => {
                Alert(strings.get('add.TOKEN_MODAL_HEADER'), `
                  <div class="TokenModal">
                      <div class="TokenModal-label">
                          ${strings.get('add.TOKEN_LABEL')}
                      </div>
                      <div class="TokenModal-value">
                          ${data.token}
                      </div>
                  </div>
                  <div class="TokenModal">
                      <div class="TokenModal-label">
                          ${strings.get('add.REFRESH_TOKEN_LABEL')}
                      </div>
                      <div class="TokenModal-value">
                          ${data.refresh_token}
                      </div>
                  </div>
                  <div class="TokenModal">
                      <div class="TokenModal-label">
                          ${strings.get('add.TOKEN_EXPIRES_LABEL')}
                      </div>
                      <div class="TokenModal-value">
                          ${$filter('longDate')(data.expires)}
                      </div>
                  </div>
                `, null, null, null, null, null, true);
                Wait('stop');
            })
            .catch(({ data, status }) => {
                ProcessErrors(null, data, status, null, {
                    hdr: strings.get('add.ERROR_HEADER'),
                    msg: `${strings.get('add.ERROR_BODY_LABEL')} ${status}`
                });
                Wait('stop');
            });
    };

    vm.form.onSaveSuccess = () => {
        $state.go('^', { user_id: $state.params.user_id }, { reload: true });
    };
}

AddTokensController.$inject = [
    'resolvedModels',
    '$state',
    'TokensStrings',
    'Rest',
    'Alert',
    'Wait',
    'GetBasePath',
    '$filter',
    'ProcessErrors'
];

export default AddTokensController;
