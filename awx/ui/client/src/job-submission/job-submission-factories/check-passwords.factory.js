export default
    function CheckPasswords(Rest, GetBasePath, ProcessErrors, Empty) {
        return function(params) {
            var scope = params.scope,
            callback = params.callback,
            credential = params.credential;

            var passwords = [];
            if (!Empty(credential)) {
                Rest.setUrl(GetBasePath('credentials')+credential);
                Rest.get()
                .success(function (data) {
                    if(data.kind === "ssh"){
                        if(data.password === "ASK" ){
                            passwords.push("ssh_password");
                        }
                        if(data.ssh_key_unlock === "ASK"){
                            passwords.push("ssh_key_unlock");
                        }
                        if(data.become_password === "ASK"){
                            passwords.push("become_password");
                        }
                        if(data.vault_password === "ASK"){
                            passwords.push("vault_password");
                        }
                    }
                    scope.$emit(callback, passwords);
                })
                .error(function (data, status) {
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
        'Empty'
    ];
