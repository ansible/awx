function AddTokensController (
    models, $state, strings, Alert, Wait,
    $filter, ProcessErrors, $scope, i18n
) {
    const vm = this || {};
    const { application, token, user } = models;

    vm.mode = 'add';
    vm.strings = strings;
    vm.panelTitle = strings.get('add.PANEL_TITLE');

    vm.form = {
        application: {
            type: 'field',
            label: i18n._('Application'),
            id: 'application',
            required: false,
            help_text: strings.get('add.APPLICATION_HELP_TEXT'),
            _resource: 'application',
            _route: 'users.edit.tokens.add.application',
            _model: application,
            _placeholder: strings.get('add.APP_PLACEHOLDER')
        },
        description: {
            type: 'String',
            label: i18n._('Description'),
            id: 'description',
            required: false
        },
        scope: {
            choices: [
                [null, ''],
                ['read', strings.get('add.SCOPE_READ_LABEL')],
                ['write', strings.get('add.SCOPE_WRITE_LABEL')]
            ],
            help_text: strings.get('add.SCOPE_HELP_TEXT'),
            id: 'scope',
            label: i18n._('Scope'),
            required: true,
            _component: 'at-input-select',
            _data: [
                [null, ''],
                ['read', strings.get('add.SCOPE_READ_LABEL')],
                ['write', strings.get('add.SCOPE_WRITE_LABEL')]
            ],
            _exp: 'choice[1] for (index, choice) in state._data',
            _format: 'selectFromOptions'
        }
    };

    vm.form.save = payload => {
        const postToken = _.has(payload, 'application') ?
            user.postAuthorizedTokens({
                id: $state.params.user_id,
                payload
            }) : token.request('post', { data: payload });

        return postToken
            .then(({ data }) => {
                const refreshHTML = data.refresh_token ?
                    `<div class="PopupModal">
                        <div class="PopupModal-label">
                            ${strings.get('add.REFRESH_TOKEN_LABEL')}
                        </div>
                        <div class="PopupModal-value">
                            ${data.refresh_token}
                        </div>
                    </div>` : '';

                Alert(strings.get('add.TOKEN_MODAL_HEADER'), `
                  <div class="PopupModal">
                      <div class="PopupModal-label">
                          ${strings.get('add.TOKEN_LABEL')}
                      </div>
                      <div class="PopupModal-value">
                          ${data.token}
                      </div>
                  </div>
                  ${refreshHTML}
                  <div class="PopupModal">
                      <div class="PopupModal-label">
                          ${strings.get('add.TOKEN_EXPIRES_LABEL')}
                      </div>
                      <div class="PopupModal-value">
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

    $scope.$watch('application', () => {
        if ($scope.application) {
            vm.form.application._idFromModal = $scope.application;
        }
    });
}

AddTokensController.$inject = [
    'resolvedModels',
    '$state',
    'TokensStrings',
    'Alert',
    'Wait',
    '$filter',
    'ProcessErrors',
    '$scope',
    'i18n'
];

export default AddTokensController;
