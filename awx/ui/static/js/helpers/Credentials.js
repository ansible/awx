/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  Credentials.js
 *
 *  Functions shared amongst Credential related controllers
 *
 */

'use strict';

angular.module('CredentialsHelper', ['Utilities'])

.factory('KindChange', ['Empty',
    function (Empty) {
        return function (params) {

            var scope = params.scope,
                reset = params.reset,
                collapse, id;

            // Put things in a default state
            scope.usernameLabel = 'Username';
            scope.aws_required = false;
            scope.rackspace_required = false;
            scope.sshKeyDataLabel = 'SSH Private Key';

            if (!Empty(scope.kind)) {
                // Apply kind specific settings
                switch (scope.kind.value) {
                case 'aws':
                    scope.aws_required = true;
                    break;
                case 'rax':
                    scope.rackspace_required = true;
                    break;
                case 'ssh':
                    scope.usernameLabel = 'SSH Username';
                    break;
                case 'scm':
                    scope.sshKeyDataLabel = 'SCM Private Key';
                    break;
                }
            }

            // Reset all the field values related to Kind.
            if (reset) {
                scope.access_key = null;
                scope.secret_key = null;
                scope.api_key = null;
                scope.username = null;
                scope.password = null;
                scope.password_confirm = null;
                scope.ssh_key_data = null;
                scope.ssh_key_unlock = null;
                scope.ssh_key_unlock_confirm = null;
                scope.sudo_username = null;
                scope.sudo_password = null;
                scope.sudo_password_confirm = null;
            }

            // Collapse or open help widget based on whether scm value is selected
            collapse = $('#credential_kind').parent().find('.panel-collapse').first();
            id = collapse.attr('id');
            if (!Empty(scope.kind) && scope.kind.value !== '') {
                if ($('#' + id + '-icon').hasClass('icon-minus')) {
                    scope.accordionToggle('#' + id);
                }
            } else {
                if ($('#' + id + '-icon').hasClass('icon-plus')) {
                    scope.accordionToggle('#' + id);
                }
            }

        };
    }
])


.factory('OwnerChange', [
    function () {
        return function (params) {
            var scope = params.scope,
                owner = scope.owner;
            if (owner === 'team') {
                scope.team_required = true;
                scope.user_required = false;
                scope.user = null;
                scope.user_username = null;
            } else {
                scope.team_required = false;
                scope.user_required = true;
                scope.team = null;
                scope.team_name = null;
            }
        };
    }
])


.factory('FormSave', ['$location', 'Alert', 'Rest', 'ProcessErrors', 'Empty', 'GetBasePath', 'CredentialForm', 'ReturnToCaller', 'Wait',
    function ($location, Alert, Rest, ProcessErrors, Empty, GetBasePath, CredentialForm, ReturnToCaller, Wait) {
        return function (params) {
            var scope = params.scope,
                mode = params.mode,
                form = CredentialForm,
                data = {}, fld, url;

            for (fld in form.fields) {
                if (fld !== 'access_key' && fld !== 'secret_key' && fld !== 'ssh_username' &&
                    fld !== 'ssh_password') {
                    if (scope[fld] === null) {
                        data[fld] = "";
                    } else {
                        data[fld] = scope[fld];
                    }
                }
            }

            if (!Empty(scope.team)) {
                data.team = scope.team;
                data.user = "";
            } else {
                data.user = scope.user;
                data.team = "";
            }

            data.kind = scope.kind.value;

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
            }

            if (Empty(data.team) && Empty(data.user)) {
                Alert('Missing User or Team', 'You must provide either a User or a Team. If this credential will only be accessed by a specific ' +
                    'user, select a User. To allow a team of users to access this credential, select a Team.', 'alert-danger');
            } else {
                Wait('start');
                if (mode === 'add') {
                    url = (!Empty(data.team)) ? GetBasePath('teams') + data.team + '/credentials/' :
                        GetBasePath('users') + data.user + '/credentials/';
                    Rest.setUrl(url);
                    Rest.post(data)
                        .success(function () {
                            Wait('stop');
                            var base = $location.path().replace(/^\//, '').split('/')[0];
                            if (base === 'credentials') {
                                ReturnToCaller();
                            }
                            ReturnToCaller(1);
                        })
                        .error(function (data, status) {
                            Wait('stop');
                            ProcessErrors(scope, data, status, form, {
                                hdr: 'Error!',
                                msg: 'Failed to create new Credential. POST status: ' + status
                            });
                        });
                } else {
                    url = GetBasePath('credentials') + scope.id + '/';
                    Rest.setUrl(url);
                    Rest.put(data)
                        .success(function () {
                            Wait('stop');
                            var base = $location.path().replace(/^\//, '').split('/')[0];
                            if (base === 'credentials') {
                                ReturnToCaller();
                            }
                            ReturnToCaller(1);
                        })
                        .error(function (data, status) {
                            Wait('stop');
                            ProcessErrors(scope, data, status, form, {
                                hdr: 'Error!',
                                msg: 'Failed to update Credential. PUT status: ' + status
                            });
                        });
                }
            }
        };
    }
]);