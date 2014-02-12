/*************************************************
 * Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  Credentials.js
 *
 *  Controller functions for the Credential model.
 *
 */

'use strict';

function CredentialsList($scope, $rootScope, $location, $log, $routeParams, Rest, Alert, CredentialList,
    GenerateList, LoadBreadCrumbs, Prompt, SearchInit, PaginateInit, ReturnToCaller,
    ClearScope, ProcessErrors, GetBasePath, SelectionInit, GetChoices, Wait, Stream) {
    
    ClearScope();

    Wait('start');

    var list = CredentialList,
        defaultUrl = GetBasePath('credentials'),
        view = GenerateList,
        base = $location.path().replace(/^\//, '').split('/')[0],
        mode = (base === 'credentials') ? 'edit' : 'select',
        url;
    
    view.inject(list, { mode: mode, scope: $scope });

    $scope.selected = [];
    $scope.credentialLoading = true;

    url = GetBasePath(base) + ( (base === 'users') ? $routeParams.user_id + '/credentials/' : $routeParams.team_id + '/credentials/' );

    if (mode === 'select') {
        SelectionInit({ scope: $scope, list: list, url: url, returnToCaller: 1 });
    }

    if ($scope.removePostRefresh) {
        $scope.removePostRefresh();
    }
    $scope.removePostRefresh = $scope.$on('PostRefresh', function () {
        // Cleanup after a delete
        var i, j;
        
        Wait('stop');
        $('#prompt-modal').off();

        list.fields.kind.searchOptions = $scope.credential_kind_options;

        // Translate the kind value
        for (i = 0; i < $scope.credentials.length; i++) {
            for (j = 0; j < $scope.credential_kind_options.length; j++) {
                if ($scope.credential_kind_options[j].value === $scope.credentials[i].kind) {
                    $scope.credentials[i].kind = $scope.credential_kind_options[j].label;
                    break;
                }
            }
        }
    });

    if ($scope.removeChoicesReady) {
        $scope.removeChoicesReady();
    }
    $scope.removeChoicesReady = $scope.$on('choicesReadyCredential', function () {
        SearchInit({
            scope: $scope,
            set: 'credentials',
            list: list,
            url: defaultUrl
        });
        PaginateInit({
            scope: $scope,
            list: list,
            url: defaultUrl
        });
        $scope.search(list.iterator);
    });

    // Load the list of options for Kind
    GetChoices({
        scope: $scope,
        url: defaultUrl,
        field: 'kind',
        variable: 'credential_kind_options',
        callback: 'choicesReadyCredential'
    });


    LoadBreadCrumbs();

    $scope.showActivity = function () {
        Stream({ scope: $scope });
    };

    $scope.addCredential = function () {
        $location.path($location.path() + '/add');
    };

    $scope.editCredential = function (id) {
        $location.path($location.path() + '/' + id);
    };

    $scope.deleteCredential = function (id, name) {

        var action = function () {
            $('#prompt-modal').on('hidden.bs.modal', function () {
                Wait('start');
            });
            $('#prompt-modal').modal('hide');
            var url = defaultUrl + id + '/';
            Rest.setUrl(url);
            Rest.destroy()
                .success(function () {
                    $scope.search(list.iterator);
                })
                .error(function (data, status) {
                    ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + ' failed. DELETE returned status: ' + status });
                });
        };

        Prompt({
            hdr: 'Delete',
            body: 'Are you sure you want to delete ' + name + '?',
            action: action
        });
    };
}

CredentialsList.$inject = ['$scope', '$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'CredentialList', 'GenerateList',
    'LoadBreadCrumbs', 'Prompt', 'SearchInit', 'PaginateInit', 'ReturnToCaller', 'ClearScope', 'ProcessErrors', 'GetBasePath',
    'SelectionInit', 'GetChoices', 'Wait', 'Stream'
];


function CredentialsAdd($scope, $rootScope, $compile, $location, $log, $routeParams, CredentialForm, GenerateForm, Rest, Alert,
    ProcessErrors, LoadBreadCrumbs, ReturnToCaller, ClearScope, GenerateList, SearchInit, PaginateInit, LookUpInit, UserList, TeamList,
    GetBasePath, GetChoices, Empty, KindChange, OwnerChange, FormSave) {
    
    ClearScope();

    // Inject dynamic view
    var form = CredentialForm,
        generator = GenerateForm,
        defaultUrl = GetBasePath('credentials'),
        url;
    
    generator.inject(form, { mode: 'add', related: false, scope: $scope });
    generator.reset();
    LoadBreadCrumbs();

    // Load the list of options for Kind
    GetChoices({
        scope: $scope,
        url: defaultUrl,
        field: 'kind',
        variable: 'credential_kind_options'
    });

    LookUpInit({
        scope: $scope,
        form: form,
        current_item: (!Empty($routeParams.user_id)) ? $routeParams.user_id : null,
        list: UserList,
        field: 'user'
    });

    LookUpInit({
        scope: $scope,
        form: form,
        current_item: (!Empty($routeParams.team_id)) ? $routeParams.team_id : null,
        list: TeamList,
        field: 'team'
    });

    if (!Empty($routeParams.user_id)) {
        // Get the username based on incoming route
        $scope.owner = 'user';
        $scope.user = $routeParams.user_id;
        OwnerChange({ scope: $scope });
        url = GetBasePath('users') + $routeParams.user_id + '/';
        Rest.setUrl(url);
        Rest.get()
            .success(function (data) {
                $scope.user_username = data.username;
            })
            .error(function (data, status) {
                ProcessErrors($scope, data, status, null, { hdr: 'Error!', msg: 'Failed to retrieve user. GET status: ' + status });
            });
    } else if (!Empty($routeParams.team_id)) {
        // Get the username based on incoming route
        $scope.owner = 'team';
        $scope.team = $routeParams.team_id;
        OwnerChange({ scope: $scope });
        url = GetBasePath('teams') + $routeParams.team_id + '/';
        Rest.setUrl(url);
        Rest.get()
            .success(function (data) {
                $scope.team_name = data.name;
            })
            .error(function (data, status) {
                ProcessErrors($scope, data, status, null, { hdr: 'Error!', msg: 'Failed to retrieve team. GET status: ' + status });
            });
    } else {
        // default type of owner to a user
        $scope.owner = 'user';
        OwnerChange({ scope: $scope });
    }

    // Handle Kind change
    $scope.kindChange = function () {
        KindChange({ scope: $scope, form: form, reset: true });
    };

    // Save
    $scope.formSave = function () {
        generator.clearApiErrors();
        FormSave({ scope: $scope, mode: 'add' });
    };

    // Handle Owner change
    $scope.ownerChange = function () {
        OwnerChange({ scope: $scope });
    };

    // Reset defaults
    $scope.formReset = function () {
        generator.reset();
    };

    // Password change
    $scope.clearPWConfirm = function (fld) {
        // If password value changes, make sure password_confirm must be re-entered
        $scope[fld] = '';
        $scope[form.name + '_form'][fld].$setValidity('awpassmatch', false);
    };

    // Respond to 'Ask at runtime?' checkbox
    $scope.ask = function (fld, associated) {
        if ($scope[fld + '_ask']) {
            $scope[fld] = 'ASK';
            $scope[associated] = '';
            $scope[form.name + '_form'][associated].$setValidity('awpassmatch', true);
        } else {
            $scope[fld] = '';
            $scope[associated] = '';
            $scope[form.name + '_form'][associated].$setValidity('awpassmatch', true);
        }
    };

    // Click clear button
    $scope.clear = function (fld, associated) {
        $scope[fld] = '';
        $scope[associated] = '';
        $scope[form.name + '_form'][associated].$setValidity('awpassmatch', true);
        $scope[form.name + '_form'].$setDirty();
    };

}

CredentialsAdd.$inject = ['$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'CredentialForm', 'GenerateForm',
    'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'ReturnToCaller', 'ClearScope', 'GenerateList', 'SearchInit', 'PaginateInit',
    'LookUpInit', 'UserList', 'TeamList', 'GetBasePath', 'GetChoices', 'Empty', 'KindChange', 'OwnerChange', 'FormSave'
];


function CredentialsEdit($scope, $rootScope, $compile, $location, $log, $routeParams, CredentialForm, GenerateForm, Rest, Alert,
    ProcessErrors, LoadBreadCrumbs, RelatedSearchInit, RelatedPaginateInit, ReturnToCaller, ClearScope, Prompt, GetBasePath, GetChoices,
    KindChange, UserList, TeamList, LookUpInit, Empty, OwnerChange, FormSave, Stream, Wait) {
    
    ClearScope();

    var defaultUrl = GetBasePath('credentials'),
        generator = GenerateForm,
        form = CredentialForm,
        base = $location.path().replace(/^\//, '').split('/')[0],
        master = {},
        id = $routeParams.credential_id;
    
    generator.inject(form, { mode: 'edit', related: true, scope: $scope });
    generator.reset();
    $scope.id = id;

    function setAskCheckboxes() {
        var fld, i;
        for (fld in form.fields) {
            if (form.fields[fld].type === 'password' && $scope[fld] === 'ASK') {
                // turn on 'ask' checkbox for password fields with value of 'ASK'
                $("#" + fld + "-clear-btn").attr("disabled", "disabled");
                $scope[fld + '_ask'] = true;
            } else {
                $scope[fld + '_ask'] = false;
                $("#" + fld + "-clear-btn").removeAttr("disabled");
            }
            master[fld + '_ask'] = $scope[fld + '_ask'];
        }

        // Set kind field to the correct option
        for (i = 0; i < $scope.credential_kind_options.length; i++) {
            if ($scope.kind === $scope.credential_kind_options[i].value) {
                $scope.kind = $scope.credential_kind_options[i];
                break;
            }
        }
    }

    if ($scope.removeCredentialLoaded) {
        $scope.removeCredentialLoaded();
    }
    $scope.removeCredentialLoaded = $scope.$on('credentialLoaded', function () {
        LookUpInit({
            scope: $scope,
            form: form,
            current_item: (!Empty($scope.user_id)) ? $scope.user_id : null,
            list: UserList,
            field: 'user'
        });

        LookUpInit({
            scope: $scope,
            form: form,
            current_item: (!Empty($scope.team_id)) ? $scope.team_id : null,
            list: TeamList,
            field: 'team'
        });

        setAskCheckboxes();
        KindChange({
            scope: $scope,
            form: form,
            reset: false
        });
        OwnerChange({ scope: $scope });
        Wait('stop');
    });

    if ($scope.removeChoicesReady) {
        $scope.removeChoicesReady();
    }
    $scope.removeChoicesReady = $scope.$on('choicesReadyCredential', function () {
        // Retrieve detail record and prepopulate the form
        Rest.setUrl(defaultUrl + ':id/');
        Rest.get({ params: { id: id } })
            .success(function (data) {
                
                var i, fld;
                
                LoadBreadCrumbs({
                    path: '/credentials/' + id,
                    title: data.name
                });

                for (fld in form.fields) {
                    if (data[fld] !== null && data[fld] !== undefined) {
                        $scope[fld] = data[fld];
                        master[fld] = $scope[fld];
                    }
                    if (form.fields[fld].type === 'lookup' && data.summary_fields[form.fields[fld].sourceModel]) {
                        $scope[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] =
                            data.summary_fields[form.fields[fld].sourceModel][form.fields[fld].sourceField];
                        master[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] =
                            $scope[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField];
                    }
                }

                if (!Empty($scope.user)) {
                    $scope.owner = 'user';
                } else {
                    $scope.owner = 'team';
                }
                master.owner = $scope.owner;

                for (i = 0; i < $scope.credential_kind_options.length; i++) {
                    if ($scope.credential_kind_options[i].value === data.kind) {
                        $scope.kind = $scope.credential_kind_options[i];
                        break;
                    }
                }
                master.kind = $scope.kind;

                switch (data.kind) {
                case 'aws':
                    $scope.access_key = data.username;
                    $scope.secret_key  = data.password;
                    master.access_key = $scope.access_key;
                    master.secret_key = $scope.secret_key;
                    break;
                case 'ssh':
                    $scope.ssh_password = data.password;
                    master.ssh_password = $scope.ssh_password;
                    break;
                case 'rax':
                    $scope.api_key = data.password;
                    master.api_key = $scope.api_key;
                    break;
                }

                $scope.$emit('credentialLoaded');
            })
            .error(function (data, status) {
                ProcessErrors($scope, data, status, form, { hdr: 'Error!',
                    msg: 'Failed to retrieve Credential: ' + $routeParams.id + '. GET status: ' + status });
            });
    });

    Wait('start');

    GetChoices({
        scope: $scope,
        url: defaultUrl,
        field: 'kind',
        variable: 'credential_kind_options',
        callback: 'choicesReadyCredential'
    });

    $scope.showActivity = function () {
        Stream({ scope: $scope });
    };

    // Save changes to the parent
    $scope.formSave = function () {
        generator.clearApiErrors();
        FormSave({ scope: $scope, mode: 'edit' });
    };

    // Handle Owner change
    $scope.ownerChange = function () {
        OwnerChange({ scope: $scope });
    };

    // Handle Kind change
    $scope.kindChange = function () {
        KindChange({ scope: $scope, form: form, reset: true });
    };

    // Cancel
    $scope.formReset = function () {
        generator.reset();
        for (var fld in master) {
            $scope[fld] = master[fld];
        }
        setAskCheckboxes();
        KindChange({ scope: $scope, form: form, reset: false });
        OwnerChange({ scope: $scope });
    };

    // Related set: Add button
    $scope.add = function (set) {
        $rootScope.flashMessage = null;
        $location.path('/' + base + '/' + $routeParams.id + '/' + set + '/add');
    };

    // Related set: Edit button
    $scope.edit = function (set, id) {
        $rootScope.flashMessage = null;
        $location.path('/' + base + '/' + $routeParams.id + '/' + set + '/' + id);
    };

    // Related set: Delete button
    $scope['delete'] = function (set, itm_id, name, title) {
        $rootScope.flashMessage = null;

        var action = function () {
            var url = defaultUrl + id + '/' + set + '/';
            Rest.setUrl(url);
            Rest.post({
                id: itm_id,
                disassociate: 1
            })
                .success(function () {
                    $('#prompt-modal').modal('hide');
                    $scope.search(form.related[set].iterator);
                })
                .error(function (data, status) {
                    $('#prompt-modal').modal('hide');
                    ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + ' failed. POST returned status: ' + status
                    });
                });
        };

        Prompt({
            hdr: 'Delete',
            body: 'Are you sure you want to remove ' + name + ' from ' + $scope.name + ' ' + title + '?',
            action: action
        });

    };

    // Password change
    $scope.clearPWConfirm = function (fld) {
        // If password value changes, make sure password_confirm must be re-entered
        $scope[fld] = '';
        $scope[form.name + '_form'][fld].$setValidity('awpassmatch', false);
    };

    // Respond to 'Ask at runtime?' checkbox
    $scope.ask = function (fld, associated) {
        if ($scope[fld + '_ask']) {
            $("#" + fld + "-clear-btn").attr("disabled", "disabled");
            $scope[fld] = 'ASK';
            $scope[associated] = '';
            $scope[form.name + '_form'][associated].$setValidity('awpassmatch', true);
        } else {
            $("#" + fld + "-clear-btn").removeAttr("disabled");
            $scope[fld] = '';
            $scope[associated] = '';
            $scope[form.name + '_form'][associated].$setValidity('awpassmatch', true);
        }
    };

    $scope.clear = function (fld, associated) {
        $scope[fld] = '';
        $scope[associated] = '';
        $scope[form.name + '_form'][associated].$setValidity('awpassmatch', true);
        $scope[form.name + '_form'].$setDirty();
    };

}

CredentialsEdit.$inject = ['$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'CredentialForm',
    'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'RelatedSearchInit', 'RelatedPaginateInit',
    'ReturnToCaller', 'ClearScope', 'Prompt', 'GetBasePath', 'GetChoices', 'KindChange', 'UserList', 'TeamList', 'LookUpInit',
    'Empty', 'OwnerChange', 'FormSave', 'Stream', 'Wait'
];