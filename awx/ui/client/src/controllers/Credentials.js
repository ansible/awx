/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/**
 * @ngdoc function
 * @name controllers.function:Credentials
 * @description This controller's for the credentials page
*/


export function CredentialsList($scope, $rootScope, $location, $log,
    $stateParams, Rest, Alert, CredentialList, GenerateList, Prompt, SearchInit,
    PaginateInit, ReturnToCaller, ClearScope, ProcessErrors, GetBasePath,
    SelectionInit, GetChoices, Wait, $state, $filter) {
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

    url = GetBasePath(base) + ( (base === 'users') ? $stateParams.user_id + '/credentials/' : $stateParams.team_id + '/credentials/' );
    if (mode === 'select') {
        SelectionInit({ scope: $scope, list: list, url: url, returnToCaller: 1 });
    }

    if ($scope.removePostRefresh) {
        $scope.removePostRefresh();
    }
    $scope.removePostRefresh = $scope.$on('PostRefresh', function () {
        var i, j;

        // Cleanup after a delete
        Wait('stop');
        $('#prompt-modal').modal('hide');

        list.fields.kind.searchOptions = $scope.credential_kind_options_list;

        // Translate the kind value
        for (i = 0; i < $scope.credentials.length; i++) {
            for (j = 0; j < $scope.credential_kind_options_list.length; j++) {
                if ($scope.credential_kind_options_list[j].value === $scope.credentials[i].kind) {
                    $scope.credentials[i].kind = $scope.credential_kind_options_list[j].label;
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
        variable: 'credential_kind_options_list',
        callback: 'choicesReadyCredential'
    });

    $scope.addCredential = function () {
        $state.transitionTo('credentials.add');
    };

    $scope.editCredential = function (id) {
        $state.transitionTo('credentials.edit', {credential_id: id});
    };

    $scope.deleteCredential = function (id, name) {
        var action = function () {
            $('#prompt-modal').modal('hide');
            Wait('start');
            var url = defaultUrl + id + '/';
            Rest.setUrl(url);
            Rest.destroy()
                .success(function () {
                    if (parseInt($state.params.credential_id) === id) {
                        $state.go("^", null, {reload: true});
                    } else {
                        $scope.search(list.iterator);
                    }
                })
                .error(function (data, status) {
                    ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + ' failed. DELETE returned status: ' + status });
                });
        };

        Prompt({
            hdr: 'Delete',
            body: '<div class="Prompt-bodyQuery">Are you sure you want to delete the credential below?</div><div class="Prompt-bodyTarget">' + $filter('sanitize')(name) + '</div>',
            action: action,
            actionText: 'DELETE'
        });
    };

    $scope.$emit('choicesReadyCredential');
}

CredentialsList.$inject = ['$scope', '$rootScope', '$location', '$log',
    '$stateParams', 'Rest', 'Alert', 'CredentialList', 'generateList', 'Prompt',
    'SearchInit', 'PaginateInit', 'ReturnToCaller', 'ClearScope',
    'ProcessErrors', 'GetBasePath', 'SelectionInit', 'GetChoices', 'Wait',
    '$state', '$filter'
];


export function CredentialsAdd($scope, $rootScope, $compile, $location, $log,
    $stateParams, CredentialForm, GenerateForm, Rest, Alert, ProcessErrors,
    ReturnToCaller, ClearScope, GenerateList, SearchInit, PaginateInit,
    LookUpInit, OrganizationList, GetBasePath, GetChoices, Empty, KindChange,
    OwnerChange, FormSave, $state, CreateSelect2) {

    ClearScope();

    // Inject dynamic view
    var form = CredentialForm,
        generator = GenerateForm,
        defaultUrl = GetBasePath('credentials'),
        url;

    $scope.keyEntered = false;

    generator.inject(form, { mode: 'add', related: false, scope: $scope });
    generator.reset();

    // Load the list of options for Kind
    GetChoices({
        scope: $scope,
        url: defaultUrl,
        field: 'kind',
        variable: 'credential_kind_options'
    });

    GetChoices({
        scope: $scope,
        url: defaultUrl,
        field: 'become_method',
        variable: 'become_options'
    });

    CreateSelect2({
        element: '#credential_become_method',
        multiple: false
    });

    CreateSelect2({
        element: '#credential_kind',
        multiple: false
    });

    $scope.canShareCredential = false;

    $rootScope.$watch('current_user', function(){
        try {
            if ($rootScope.current_user.is_superuser) {
                $scope.canShareCredential = true;
            } else {
                Rest.setUrl(`/api/v1/users/${$rootScope.current_user.id}/admin_of_organizations`);
                Rest.get()
                    .success(function(data) {
                        $scope.canShareCredential = (data.count) ? true : false;
                    }).error(function (data, status) {
                        ProcessErrors($scope, data, status, null, { hdr: 'Error!', msg: 'Failed to find if users is admin of org' + status });
                    });
            }


            var orgUrl = ($rootScope.current_user.is_superuser) ?
                GetBasePath("organizations") :
                $rootScope.current_user.url + "admin_of_organizations?";

            // Create LookUpInit for organizations
            LookUpInit({
                scope: $scope,
                url: orgUrl,
                form: form,
                list: OrganizationList,
                field: 'organization',
                input_type: 'radio',
                autopopulateLookup: false
            });
        }
        catch(err){
            // $rootScope.current_user isn't available because a call to the config endpoint hasn't finished resolving yet
        }
    });

    if (!Empty($stateParams.user_id)) {
        // Get the username based on incoming route
        $scope.owner = 'user';
        $scope.user = $stateParams.user_id;
        OwnerChange({ scope: $scope });
        url = GetBasePath('users') + $stateParams.user_id + '/';
        Rest.setUrl(url);
        Rest.get()
            .success(function (data) {
                $scope.user_username = data.username;
            })
            .error(function (data, status) {
                ProcessErrors($scope, data, status, null, { hdr: 'Error!', msg: 'Failed to retrieve user. GET status: ' + status });
            });
    } else if (!Empty($stateParams.team_id)) {
        // Get the username based on incoming route
        $scope.owner = 'team';
        $scope.team = $stateParams.team_id;
        OwnerChange({ scope: $scope });
        url = GetBasePath('teams') + $stateParams.team_id + '/';
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

    $scope.$watch("ssh_key_data", function(val) {
        if (val === "" || val === null || val === undefined) {
            $scope.keyEntered = false;
            $scope.ssh_key_unlock_ask = false;
            $scope.ssh_key_unlock = "";
        } else {
            $scope.keyEntered = true;
        }
    });

    // Handle Kind change
    $scope.kindChange = function () {
        KindChange({ scope: $scope, form: form, reset: true });
    };

    // Save
    $scope.formSave = function () {
        generator.clearApiErrors();
        generator.checkAutoFill();
        if ($scope[form.name + '_form'].$valid) {
            FormSave({ scope: $scope, mode: 'add' });
        }
    };

    $scope.formCancel = function () {
        $state.transitionTo('credentials');
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
            $("#" + form.name + "_" + fld + "_input").attr("type", "text");
            $("#" + form.name + "_" + fld + "_show_input_button").html("Hide");
            if (associated !== "undefined") {
                $("#" + form.name + "_" + fld + "_input").attr("type", "password");
                $("#" + form.name + "_" + fld + "_show_input_button").html("Show");
                $scope[associated] = '';
                $scope[form.name + '_form'][associated].$setValidity('awpassmatch', true);
            }
        } else {
            $scope[fld] = '';
            $("#" + form.name + "_" + fld + "_input").attr("type", "password");
            $("#" + form.name + "_" + fld + "_show_input_button").html("Show");
            if (associated !== "undefined") {
                $("#" + form.name + "_" + fld + "_input").attr("type", "text");
                $("#" + form.name + "_" + fld + "_show_input_button").html("Hide");
                $scope[associated] = '';
                $scope[form.name + '_form'][associated].$setValidity('awpassmatch', true);
            }
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

CredentialsAdd.$inject = ['$scope', '$rootScope', '$compile', '$location',
    '$log', '$stateParams', 'CredentialForm', 'GenerateForm', 'Rest', 'Alert',
    'ProcessErrors', 'ReturnToCaller', 'ClearScope', 'generateList',
    'SearchInit', 'PaginateInit', 'LookUpInit', 'OrganizationList',
    'GetBasePath', 'GetChoices', 'Empty', 'KindChange', 'OwnerChange',
    'FormSave', '$state', 'CreateSelect2'
];


export function CredentialsEdit($scope, $rootScope, $compile, $location, $log,
    $stateParams, CredentialForm, GenerateForm, Rest, Alert, ProcessErrors,
    RelatedSearchInit, RelatedPaginateInit, ReturnToCaller, ClearScope, Prompt,
    GetBasePath, GetChoices, KindChange, OrganizationList, LookUpInit, Empty,
    OwnerChange, FormSave, Wait, $state, CreateSelect2, Authorization) {
    if (!$rootScope.current_user) {
        Authorization.restoreUserInfo();
    }

    ClearScope();
    var defaultUrl = GetBasePath('credentials'),
        generator = GenerateForm,
        form = CredentialForm,
        base = $location.path().replace(/^\//, '').split('/')[0],
        master = {},
        id = $stateParams.credential_id,
        relatedSets = {};
    generator.inject(form, { mode: 'edit', related: true, scope: $scope });
    generator.reset();
    $scope.id = id;

    $scope.canShareCredential = false;

    if ($rootScope.current_user.is_superuser) {
        $scope.canShareCredential = true;
    } else {
        Rest.setUrl(`/api/v1/users/${$rootScope.current_user.id}/admin_of_organizations`);
        Rest.get()
            .success(function(data) {
                $scope.canShareCredential = (data.count) ? true : false;
            }).error(function (data, status) {
                ProcessErrors($scope, data, status, null, { hdr: 'Error!', msg: 'Failed to find if users is admin of org' + status });
            });
    }

    function setAskCheckboxes() {
        var fld, i;
        for (fld in form.fields) {
            if (form.fields[fld].type === 'sensitive' && $scope[fld] === 'ASK') {
                // turn on 'ask' checkbox for password fields with value of 'ASK'
                $("#" + form.name + "_" + fld + "_input").attr("type", "text");
                $("#" + form.name + "_" + fld + "_show_input_button").html("Hide");
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
        var set;
        for (set in relatedSets) {
            $scope.search(relatedSets[set].iterator);
        }
        var orgUrl = ($rootScope.current_user.is_superuser) ?
            GetBasePath("organizations") :
            $rootScope.current_user.url + "admin_of_organizations?";

        // create LookUpInit for organizations
        LookUpInit({
            scope: $scope,
            url: orgUrl,
            form: form,
            current_item: $scope.organization,
            list: OrganizationList,
            field: 'organization',
            input_type: 'radio',
            autopopulateLookup: false
        });

        setAskCheckboxes();
        KindChange({
            scope: $scope,
            form: form,
            reset: false
        });
        OwnerChange({ scope: $scope });
        $scope.$watch("ssh_key_data", function(val) {
            if (val === "" || val === null || val === undefined) {
                $scope.keyEntered = false;
                $scope.ssh_key_unlock_ask = false;
                $scope.ssh_key_unlock = "";
            } else {
                $scope.keyEntered = true;
            }
        });
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
                if (data && data.summary_fields &&
                    data.summary_fields.organization &&
                    data.summary_fields.organization.id) {
                    $scope.needsRoleList = true;
                } else {
                    $scope.needsRoleList = false;
                }

                $scope.credential_name = data.name;

                var i, fld;


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
                relatedSets = form.relatedSets(data.related);

                if (!Empty($scope.user)) {
                    $scope.owner = 'user';
                } else {
                    $scope.owner = 'team';
                }
                master.owner = $scope.owner;

                for (i = 0; i < $scope.become_options.length; i++) {
                    if ($scope.become_options[i].value === data.become_method) {
                        $scope.become_method = $scope.become_options[i];
                        break;
                    }
                }

                if ($scope.become_method && $scope.become_method.value === "") {
                    $scope.become_method = null;
                }
                master.become_method = $scope.become_method;

                $scope.$watch('become_method', function(val) {
                    if (val !== null) {
                        if (val.value === "") {
                            $scope.become_username = "";
                            $scope.become_password = "";
                        }
                    }
                });

                for (i = 0; i < $scope.credential_kind_options.length; i++) {
                    if ($scope.credential_kind_options[i].value === data.kind) {
                        $scope.kind = $scope.credential_kind_options[i];
                        break;
                    }
                }
                master.kind = $scope.kind;

                CreateSelect2({
                    element: '#credential_become_method',
                    multiple: false
                });

                CreateSelect2({
                    element: '#credential_kind',
                    multiple: false
                });

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
                case 'gce':
                    $scope.email_address = data.username;
                    $scope.project = data.project;
                    break;
                case 'azure':
                    $scope.subscription = data.username;
                    break;
                }
                $scope.credential_obj = data;

                RelatedSearchInit({
                    scope: $scope,
                    form: form,
                    relatedSets: relatedSets
                });
                RelatedPaginateInit({
                    scope: $scope,
                    relatedSets: relatedSets
                });

                $scope.$emit('credentialLoaded');
            })
            .error(function (data, status) {
                ProcessErrors($scope, data, status, form, { hdr: 'Error!',
                    msg: 'Failed to retrieve Credential: ' + $stateParams.id + '. GET status: ' + status });
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

    GetChoices({
        scope: $scope,
        url: defaultUrl,
        field: 'become_method',
        variable: 'become_options'
    });

    // Save changes to the parent
    $scope.formSave = function () {
        generator.clearApiErrors();
        generator.checkAutoFill({ scope: $scope });
        if ($scope[form.name + '_form'].$valid) {
            FormSave({ scope: $scope, mode: 'edit' });
        }
    };

    // Handle Owner change
    $scope.ownerChange = function () {
        OwnerChange({ scope: $scope });
    };

    // Handle Kind change
    $scope.kindChange = function () {
        KindChange({ scope: $scope, form: form, reset: true });
    };

    $scope.formCancel = function () {
        $state.transitionTo('credentials');
    };

    // Related set: Add button
    $scope.add = function (set) {
        $rootScope.flashMessage = null;
        $location.path('/' + base + '/' + $stateParams.id + '/' + set + '/add');
    };

    // Related set: Edit button
    $scope.edit = function (set, id) {
        $rootScope.flashMessage = null;
        $location.path('/' + base + '/' + $stateParams.id + '/' + set + '/' + id);
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
            body: '<div class="Prompt-bodyQuery">Are you sure you want to remove the ' + title + ' below from ' + $scope.name + '?</div><div class="Prompt-bodyTarget">' + name + '</div>',
            action: action,
            actionText: 'DELETE'
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
            $scope[fld] = 'ASK';
            $("#" + form.name + "_" + fld + "_input").attr("type", "text");
            $("#" + form.name + "_" + fld + "_show_input_button").html("Hide");
            if (associated !== "undefined") {
                $("#" + form.name + "_" + fld + "_input").attr("type", "password");
                $("#" + form.name + "_" + fld + "_show_input_button").html("Show");
                $scope[associated] = '';
                $scope[form.name + '_form'][associated].$setValidity('awpassmatch', true);
            }
        } else {
            $scope[fld] = '';
            $("#" + form.name + "_" + fld + "_input").attr("type", "password");
            $("#" + form.name + "_" + fld + "_show_input_button").html("Show");
            if (associated !== "undefined") {
                $("#" + form.name + "_" + fld + "_input").attr("type", "text");
                $("#" + form.name + "_" + fld + "_show_input_button").html("Hide");
                $scope[associated] = '';
                $scope[form.name + '_form'][associated].$setValidity('awpassmatch', true);
            }
        }
    };

    $scope.clear = function (fld, associated) {
        $scope[fld] = '';
        $scope[associated] = '';
        $scope[form.name + '_form'][associated].$setValidity('awpassmatch', true);
        $scope[form.name + '_form'].$setDirty();
    };

}

CredentialsEdit.$inject = ['$scope', '$rootScope', '$compile', '$location',
    '$log', '$stateParams', 'CredentialForm', 'GenerateForm', 'Rest', 'Alert',
    'ProcessErrors', 'RelatedSearchInit', 'RelatedPaginateInit',
    'ReturnToCaller', 'ClearScope', 'Prompt', 'GetBasePath', 'GetChoices',
    'KindChange', 'OrganizationList', 'LookUpInit', 'Empty', 'OwnerChange',
    'FormSave', 'Wait', '$state', 'CreateSelect2', 'Authorization'
];
