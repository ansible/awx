/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', '$rootScope', '$stateParams', 'CredentialForm',
    'GenerateForm', 'Rest', 'ProcessErrors', 'ClearScope', 'GetBasePath',
    'GetChoices', 'Empty', 'KindChange', 'BecomeMethodChange',
    'OwnerChange', 'CredentialFormSave', '$state', 'CreateSelect2', 'i18n',
    function($scope, $rootScope, $stateParams, CredentialForm, GenerateForm,
    Rest, ProcessErrors, ClearScope, GetBasePath, GetChoices, Empty, KindChange,
    BecomeMethodChange, OwnerChange, CredentialFormSave, $state, CreateSelect2, i18n) {

        ClearScope();

        // Inject dynamic view
        var form = CredentialForm,
            defaultUrl = GetBasePath('credentials'),
            url;

        init();

        function init() {
            $scope.canEditOrg = true;
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

            // apply form definition's default field values
            GenerateForm.applyDefaults(form, $scope);

            $scope.keyEntered = false;
            $scope.permissionsTooltip = i18n._('Please save before assigning permissions');

            // determine if the currently logged-in user may share this credential
            // previous commentary said: "$rootScope.current_user isn't available because a call to the config endpoint hasn't finished resolving yet"
            // I'm 99% sure this state's will never resolve block will be rejected if setup surrounding config endpoint hasn't completed
            if ($rootScope.current_user && $rootScope.current_user.is_superuser) {
                $scope.canShareCredential = true;
            } else {
                Rest.setUrl(`/api/v1/users/${$rootScope.current_user.id}/admin_of_organizations`);
                Rest.get()
                    .success(function(data) {
                        $scope.canShareCredential = (data.count) ? true : false;
                    }).error(function(data, status) {
                        ProcessErrors($scope, data, status, null, { hdr: 'Error!', msg: 'Failed to find if users is admin of org' + status });
                    });
            }
        }

        if (!Empty($stateParams.user_id)) {
            // Get the username based on incoming route
            $scope.owner = 'user';
            $scope.user = $stateParams.user_id;
            OwnerChange({ scope: $scope });
            url = GetBasePath('users') + $stateParams.user_id + '/';
            Rest.setUrl(url);
            Rest.get()
                .success(function(data) {
                    $scope.user_username = data.username;
                })
                .error(function(data, status) {
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
                .success(function(data) {
                    $scope.team_name = data.name;
                })
                .error(function(data, status) {
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
        $scope.kindChange = function() {
            KindChange({ scope: $scope, form: form, reset: true });
        };

        $scope.becomeMethodChange = function() {
            BecomeMethodChange({ scope: $scope });
        };

        // Save
        $scope.formSave = function() {
            if ($scope[form.name + '_form'].$valid) {
                CredentialFormSave({ scope: $scope, mode: 'add' });
            }
        };

        $scope.formCancel = function() {
            $state.go('credentials');
        };

        // Password change
        $scope.clearPWConfirm = function(fld) {
            // If password value changes, make sure password_confirm must be re-entered
            $scope[fld] = '';
            $scope[form.name + '_form'][fld].$setValidity('awpassmatch', false);
        };

        // Respond to 'Ask at runtime?' checkbox
        $scope.ask = function(fld, associated) {
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
        $scope.clear = function(fld, associated) {
            $scope[fld] = '';
            $scope[associated] = '';
            $scope[form.name + '_form'][associated].$setValidity('awpassmatch', true);
            $scope[form.name + '_form'].$setDirty();
        };
    }
];
