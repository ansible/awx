export default
    function CredentialFormSave($rootScope, $location, Rest, ProcessErrors, GetBasePath, CredentialForm, ReturnToCaller, Wait, $state, i18n) {
        return function(params) {
            var scope = params.scope,
            mode = params.mode,
            form = CredentialForm,
            data = {}, fld, url;

            for (fld in form.fields) {
                if (fld !== 'access_key' && fld !== 'secret_key' && fld !== 'ssh_username' &&
                    fld !== 'ssh_password') {
                    if (fld === "organization" && !scope[fld]) {
                        data.user = $rootScope.current_user.id;
                    } else if (scope[fld] === null) {
                        data[fld] = "";
                    } else {
                        data[fld] = scope[fld];
                    }
                }
            }

            data.kind = scope.kind.value;
            if (scope.become_method === null || typeof scope.become_method === 'undefined') {
               data.become_method = "";
               data.become_username = "";
               data.become_password = "";
            } else {
               data.become_method = (scope.become_method.value) ? scope.become_method.value : "";
            }
            switch (data.kind) {
                case 'ssh':
                    data.password = scope.ssh_password;
                break;
                case 'aws':
                    data.username = scope.access_key;
                data.password = scope.secret_key;
                break;
                case 'rax':
                    data.password = scope.api_key;
                break;
                case 'gce':
                    data.username = scope.email_address;
                data.project = scope.project;
                break;
                case 'azure':
                    data.username = scope.subscription;
            }

            Wait('start');
            if (mode === 'add') {
                url = GetBasePath("credentials");
                Rest.setUrl(url);
                Rest.post(data)
                .then(({data}) => {
                    scope.addedItem = data.id;

                    Wait('stop');
                    var base = $location.path().replace(/^\//, '').split('/')[0];
                    if (base === 'credentials') {
                        $state.go('credentials.edit', {credential_id: data.id}, {reload: true});
                    }
                    else {
                        ReturnToCaller(1);
                    }
                })
                .catch(({data, status}) => {
                    Wait('stop');
                    // TODO: hopefully this conditional error handling will to away in a future versions.  The reason why we cannot
                    // simply pass this error to ProcessErrors is because it will actually match the form element 'ssh_key_unlock' and show
                    // the error there.  The ssh_key_unlock field is not shown when the kind of credential is gce/azure and as a result the
                    // error is never shown.  In the future, the API will hopefully either behave or respond differently.
                    if(status && status === 400 && data && data.ssh_key_unlock && (scope.kind.value === 'gce' || scope.kind.value === 'azure')) {
                        scope.ssh_key_data_api_error = i18n._("Encrypted credentials are not supported.");
                    }
                    else {
                        ProcessErrors(scope, data, status, form, {
                            hdr: i18n._('Error!'),
                            msg: i18n._('Failed to create new Credential. POST status: ') + status
                        });
                    }
                });
            } else {
                url = GetBasePath('credentials') + scope.id + '/';
                Rest.setUrl(url);
                Rest.put(data)
                .then(() => {
                    Wait('stop');
                    $state.go($state.current, {}, {reload: true});
                })
                .catch(({data, status}) => {
                    Wait('stop');
                    ProcessErrors(scope, data, status, form, {
                        hdr: i18n._('Error!'),
                        msg: i18n._('Failed to update Credential. PUT status: ') + status
                    });
                });
           }
        };
    }

CredentialFormSave.$inject =
    [   '$rootScope', '$location', 'Rest',
        'ProcessErrors', 'GetBasePath', 'CredentialForm',
        'ReturnToCaller', 'Wait', '$state', 'i18n'
    ];
