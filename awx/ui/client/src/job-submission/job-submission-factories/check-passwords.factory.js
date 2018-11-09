export default
    function CheckPasswords(Rest, GetBasePath, ProcessErrors, Empty, credentialTypesLookup) {
        return function(params) {
            var scope = params.scope,
            callback = params.callback,
            credential = params.credential;

            var passwords = [];
            if (!Empty(credential)) {
                Rest.setUrl(GetBasePath('credentials')+credential);
                Rest.get()
                .then(({data}) => {
                    credentialTypesLookup()
                        .then(kinds => {
                            if(data.credential_type === kinds.ssh && data.inputs){
                                if(data.inputs.password === "ASK" ){
                                    passwords.push("ssh_password");
                                }
                                if(data.inputs.ssh_key_unlock === "ASK"){
                                    passwords.push("ssh_key_unlock");
                                }
                                if(data.inputs.become_password === "ASK"){
                                    passwords.push("become_password");
                                }
                                if(data.inputs.vault_password === "ASK"){
                                    passwords.push("vault_password");
                                }
                            }
                            scope.$emit(callback, passwords);
                        });

                })
                .catch(({data, status}) => {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                    msg: 'Failed to get job template details. GET returned status: ' + status });
                });
            }

        };
    }

CheckPasswords.$inject =
    [   'Rest',
        'GetBasePath',
        'ProcessErrors',
        'Empty',
        'credentialTypesLookup'
    ];
