/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default [
    '$scope',
    '$rootScope',
    '$stateParams',
    'SettingsUtils',
    'CreateSelect2',
    'GenerateForm',
    'i18n',
    'ParseTypeChange',
    function (
        $scope,
        $rootScope,
        $stateParams,
        SettingsUtils,
        CreateSelect2,
        GenerateForm,
        i18n,
        ParseTypeChange
    ) {
        const authVm = this;
        const generator = GenerateForm;
        const formTracker = $scope.$parent.vm.formTracker; // track the current active form

        authVm.activeAuthForm = 'azure';
        authVm.activeTab = 'azure';
        authVm.ldapDropdownValue = '';
        authVm.githubDropdownValue = 'github';

        let codeInputInitialized = false;

        const formDefs = $scope.$parent.formDefs;

        // Default active authform
        if ($stateParams.form === 'auth') {
            formTracker.setCurrentAuth(authVm.activeAuthForm);
        }

        authVm.activeForm = function(tab) {
            if(!_.get($scope.$parent, [formTracker.currentFormName(), '$dirty'])) {
                authVm.activeTab = tab;
                authVm.activeAuthForm = getActiveAuthForm(tab);
                formTracker.setCurrentAuth(authVm.activeAuthForm);
                startCodeMirrors();
            } else {
                var msg = i18n._('You have unsaved changes. Would you like to proceed <strong>without</strong> saving?');
                var title = i18n._('Warning: Unsaved Changes');
                var buttons = [{
                    label: i18n._('Discard changes'),
                    "class": "btn Form-cancelButton",
                    "id": "formmodal-cancel-button",
                    onClick: function() {
                        $scope.$parent.vm.populateFromApi();
                        $scope.$parent[formTracker.currentFormName()].$setPristine();
                        authVm.activeTab = tab;
                        authVm.activeAuthForm = getActiveAuthForm(tab);
                        formTracker.setCurrentAuth(authVm.activeAuthForm);
                        $('#FormModal-dialog').dialog('close');
                    }
                }, {
                    label: i18n._('Save changes'),
                    onClick: function() {
                        $scope.$parent.vm.formSave()
                        .then(function() {
                            $scope.$parent[formTracker.currentFormName()].$setPristine();
                            $scope.$parent.vm.populateFromApi();
                            authVm.activeTab = tab;
                            authVm.activeAuthForm = getActiveAuthForm(tab);
                            formTracker.setCurrentAuth(authVm.activeAuthForm);
                            $('#FormModal-dialog').dialog('close');
                        }).catch(() => {
                            event.preventDefault();
                            $('#FormModal-dialog').dialog('close');
                        });
                    },
                    "class": "btn btn-primary",
                    "id": "formmodal-save-button"
                }];
                $scope.$parent.vm.triggerModal(msg, title, buttons);
            }
            formTracker.setCurrentAuth(authVm.activeAuthForm);
            authVm.ldapSelected = (authVm.activeAuthForm.indexOf('ldap') !== -1);
        };

        authVm.dropdownOptions = [
            {label: i18n._('Azure AD'), value: 'azure'},
            {label: i18n._('GitHub'), value: 'github'},
            {label: i18n._('Google OAuth2'), value: 'google_oauth'},
            {label: i18n._('LDAP'), value: 'ldap'},
            {label: i18n._('RADIUS'), value: 'radius'},
            {label: i18n._('SAML'), value: 'saml'},
            {label: i18n._('TACACS+'), value: 'tacacs'}
        ];

        authVm.ldapDropdownOptions = [
            {label: i18n._('Default'), value: ''},
            {label: i18n._('LDAP 1 (Optional)'), value: '1'},
            {label: i18n._('LDAP 2 (Optional)'), value: '2'},
            {label: i18n._('LDAP 3 (Optional)'), value: '3'},
            {label: i18n._('LDAP 4 (Optional)'), value: '4'},
            {label: i18n._('LDAP 5 (Optional)'), value: '5'},
        ];

        authVm.githubDropdownOptions = [
            {label: i18n._('GitHub (Default)'), value: 'github'},
            {label: i18n._('GitHub Org'), value: 'github_org'},
            {label: i18n._('GitHub Team'), value: 'github_team'},
        ];

        CreateSelect2({
            element: '#configure-dropdown-nav',
            multiple: false,
        });

        CreateSelect2({
            element: '#configure-ldap-dropdown',
            multiple: false,
        });

        CreateSelect2({
            element: '#configure-github-dropdown',
            multiple: false,
        });

        var authForms = [
            {
                formDef: formDefs.azure,
                id: 'auth-azure-form',
                name: 'azure'
            },
            {
                formDef: formDefs.github,
                id: 'auth-github-form',
                name: 'github'
            },
            {
                formDef: formDefs.github_org,
                id: 'auth-github-org-form',
                name: 'github_org'
            },
            {
                formDef: formDefs.github_team,
                id: 'auth-github-team-form',
                name: 'github_team'
            },
            {
                formDef: formDefs.google_oauth,
                id: 'auth-google-form',
                name: 'google_oauth'
            },
            {
                formDef: formDefs.radius,
                id: 'auth-radius-form',
                name: 'radius'
            },
            {
                formDef: formDefs.tacacs,
                id: 'auth-tacacs-form',
                name: 'tacacs'
            },
            {
                formDef: formDefs.saml,
                id: 'auth-saml-form',
                name: 'saml'
            },
            {
                formDef: formDefs.ldap,
                id: 'auth-ldap-form',
                name: 'ldap'
            },
            {
                formDef: formDefs.ldap1,
                id: 'auth-ldap1-form',
                name: 'ldap1'
            },
            {
                formDef: formDefs.ldap2,
                id: 'auth-ldap2-form',
                name: 'ldap2'
            },
            {
                formDef: formDefs.ldap3,
                id: 'auth-ldap3-form',
                name: 'ldap3'
            },
            {
                formDef: formDefs.ldap4,
                id: 'auth-ldap4-form',
                name: 'ldap4'
            },
            {
                formDef: formDefs.ldap5,
                id: 'auth-ldap5-form',
                name: 'ldap5'
            }
        ];
        var forms = _.map(authForms, 'formDef');
        _.each(forms, function(form) {
            var keys = _.keys(form.fields);
            _.each(keys, function(key) {
                if($scope.configDataResolve[key].type === 'choice') {
                    // Create options for dropdowns
                    var optionsGroup = key + '_options';
                    $scope.$parent.$parent[optionsGroup] = [];
                    _.each($scope.configDataResolve[key].choices, function(choice){
                        $scope.$parent.$parent[optionsGroup].push({
                            name: choice[0],
                            label: choice[1],
                            value: choice[0]
                        });
                    });
                }
                addFieldInfo(form, key);
            });
            // Disable the save button for system auditors
            form.buttons.save.disabled = $rootScope.user_is_system_auditor;
        });

        $scope.$parent.$parent.parseType = 'json';

        _.each(authForms, function(form) {
            // Generate the forms
            generator.inject(form.formDef, {
                id: form.id,
                mode: 'edit',
                scope: $scope.$parent.$parent,
                related: true,
                noPanel: true
            });
        });

        function startCodeMirrors (key) {
            var form = _.find(authForms, f => f.name === $scope.authVm.activeAuthForm);

            if(!key){
                // Attach codemirror to fields that need it
                _.each(form.formDef.fields, function(field) {
                    // Codemirror balks at empty values so give it one
                    if($scope.$parent.$parent[field.name] === null && field.codeMirror) {
                      $scope.$parent.$parent[field.name] = '{}';
                    }
                    if(field.codeMirror) {
                        createIt(field.name);
                    }
                });
            }
            else if(key){
                createIt(key);
            }

            function createIt(name){
                ParseTypeChange({
                   scope: $scope.$parent.$parent,
                   variable: name,
                   parse_variable: 'parseType',
                   field_id: form.formDef.name + '_' + name,
                   readOnly: $scope.configDataResolve[name] && $scope.configDataResolve[name].disabled ? true : false
                 });
                 $scope.parseTypeChange('parseType', name);
            }
        }

        function addFieldInfo(form, key) {
            _.extend(form.fields[key], {
                awPopOver: ($scope.configDataResolve[key].defined_in_file) ?
                    null: $scope.configDataResolve[key].help_text,
                label: $scope.configDataResolve[key].label,
                name: key,
                toggleSource: key,
                dataPlacement: 'top',
                placeholder: SettingsUtils.formatPlaceholder($scope.configDataResolve[key].placeholder, key) || null,
                dataTitle: $scope.configDataResolve[key].label,
                required: $scope.configDataResolve[key].required,
                ngDisabled: $rootScope.user_is_system_auditor,
                disabled: $scope.configDataResolve[key].disabled || null,
                readonly: $scope.configDataResolve[key].readonly || null,
                definedInFile: $scope.configDataResolve[key].defined_in_file || null
            });
        }

        // Flag to avoid re-rendering and breaking Select2 dropdowns on tab switching
        var dropdownRendered = false;

        function populateLDAPGroupType(flag, index = null){
            let groupPropName;
            let groupOptionsPropName;
            let selectElementId;

            if (index) {
                groupPropName = `AUTH_LDAP_${index}_GROUP_TYPE`;
                groupOptionsPropName = `${groupPropName}_options`;
                selectElementId = `#configuration_ldap${index}_template_${groupPropName}`;
            } else {
                groupPropName = 'AUTH_LDAP_GROUP_TYPE';
                groupOptionsPropName = `${groupPropName}_options`;
                selectElementId = `#configuration_ldap_template_${groupPropName}`;
            }

            if($scope.$parent[groupPropName] !== null) {
                $scope.$parent.$parent[groupPropName] = _.find($scope[groupOptionsPropName], { value: $scope.$parent[groupPropName] });
            }

            if(flag !== undefined){
                dropdownRendered = flag;
            }

            if(!dropdownRendered) {
                dropdownRendered = true;
                CreateSelect2({
                    element: selectElementId,
                    multiple: false,
                    placeholder: i18n._('Select group types'),
                });
            }
        }

        function populateTacacsProtocol(flag){
            if($scope.$parent.TACACSPLUS_AUTH_PROTOCOL !== null) {
                $scope.$parent.$parent.TACACSPLUS_AUTH_PROTOCOL = _.find($scope.$parent.TACACSPLUS_AUTH_PROTOCOL_options, { value: $scope.$parent.TACACSPLUS_AUTH_PROTOCOL });
            }

            if(flag !== undefined){
                dropdownRendered = flag;
            }

            if(!dropdownRendered) {
                dropdownRendered = true;
                CreateSelect2({
                    element: '#configuration_tacacs_template_TACACSPLUS_AUTH_PROTOCOL',
                    multiple: false,
                    placeholder: i18n._('Select group types'),
                });
            }
        }

        $scope.$on('AUTH_LDAP_GROUP_TYPE_populated', (e, data, flag) => populateLDAPGroupType(flag));
        $scope.$on('AUTH_LDAP_1_GROUP_TYPE_populated', (e, data, flag) => populateLDAPGroupType(flag, 1));
        $scope.$on('AUTH_LDAP_2_GROUP_TYPE_populated', (e, data, flag) => populateLDAPGroupType(flag, 2));
        $scope.$on('AUTH_LDAP_3_GROUP_TYPE_populated', (e, data, flag) => populateLDAPGroupType(flag, 3));
        $scope.$on('AUTH_LDAP_4_GROUP_TYPE_populated', (e, data, flag) => populateLDAPGroupType(flag, 4));
        $scope.$on('AUTH_LDAP_5_GROUP_TYPE_populated', (e, data, flag) => populateLDAPGroupType(flag, 5));

        $scope.$on('$locationChangeStart', (event, url) => {
            let parts = url.split('/');
            let tab = parts[parts.length - 1];

            if (tab === 'auth') {
                startCodeMirrors();
                codeInputInitialized = true;
            }
        });

        $scope.$on('populated', function() {
            let tab = $stateParams.form;

            if (tab === 'auth') {
                startCodeMirrors();
                codeInputInitialized = true;
            }

            populateLDAPGroupType(false);
            populateLDAPGroupType(false, 1);
            populateLDAPGroupType(false, 2);
            populateLDAPGroupType(false, 3);
            populateLDAPGroupType(false, 4);
            populateLDAPGroupType(false, 5);

            populateTacacsProtocol(false);
        });

        $scope.$on('codeMirror_populated', function() {
            let tab = $stateParams.form;
            if (tab === 'auth') {
                startCodeMirrors();
                codeInputInitialized = true;
            }
        });

        function getActiveAuthForm (tab) {
            if (tab === 'ldap') {
                return `ldap${authVm.ldapDropdownValue}`;
            } else if (tab === 'github') {
                return authVm.githubDropdownValue;
            }
            return tab;
        }

        angular.extend(authVm, {
            authForms: authForms,
        });
    }
];
