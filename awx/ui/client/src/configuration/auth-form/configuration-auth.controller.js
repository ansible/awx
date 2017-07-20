/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default [
    '$scope',
    '$rootScope',
    '$state',
    '$stateParams',
    '$timeout',
    '$q',
    'configurationAzureForm',
    'configurationGithubForm',
    'configurationGithubOrgForm',
    'configurationGithubTeamForm',
    'configurationGoogleForm',
    'configurationLdapForm',
    'configurationRadiusForm',
    'configurationTacacsForm',
    'configurationSamlForm',
    'ConfigurationService',
    'ConfigurationUtils',
    'CreateSelect2',
    'GenerateForm',
    'i18n',
    'ParseTypeChange',
    function(
        $scope,
        $rootScope,
        $state,
        $stateParams,
        $timeout,
        $q,
        configurationAzureForm,
        configurationGithubForm,
        configurationGithubOrgForm,
        configurationGithubTeamForm,
        configurationGoogleForm,
        configurationLdapForm,
        configurationRadiusForm,
        configurationTacacsForm,
        configurationSamlForm,
        ConfigurationService,
        ConfigurationUtils,
        CreateSelect2,
        GenerateForm,
        i18n,
        ParseTypeChange
    ) {
        var authVm = this;

        var generator = GenerateForm;
        var formTracker = $scope.$parent.vm.formTracker;
        var dropdownValue = 'azure';
        var activeAuthForm = 'azure';
        let codeInputInitialized = false;

        // Default active form
        if ($stateParams.currentTab === '' || $stateParams.currentTab === 'auth') {
            formTracker.setCurrentAuth(activeAuthForm);
        }

        var activeForm = function() {

            if(!$scope.$parent[formTracker.currentFormName()].$dirty) {
                authVm.activeAuthForm = authVm.dropdownValue;
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
                        authVm.activeAuthForm = authVm.dropdownValue;
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
                            authVm.activeAuthForm = authVm.dropdownValue;
                            formTracker.setCurrentAuth(authVm.activeAuthForm);
                            $('#FormModal-dialog').dialog('close');
                        });
                    },
                    "class": "btn btn-primary",
                    "id": "formmodal-save-button"
                }];
                $scope.$parent.vm.triggerModal(msg, title, buttons);
            }
            formTracker.setCurrentAuth(authVm.activeAuthForm);
        };

        var dropdownOptions = [
            {label: i18n._('Azure AD'), value: 'azure'},
			{label: i18n._('GitHub'), value: 'github'},
            {label: i18n._('GitHub Org'), value: 'github_org'},
            {label: i18n._('GitHub Team'), value: 'github_team'},
            {label: i18n._('Google OAuth2'), value: 'google_oauth'},
            {label: i18n._('LDAP'), value: 'ldap'},
            {label: i18n._('RADIUS'), value: 'radius'},
            {label: i18n._('SAML'), value: 'saml'},
            {label: i18n._('TACACS+'), value: 'tacacs'}
        ];

        CreateSelect2({
            element: '#configure-dropdown-nav',
            multiple: false,
        });

        var authForms = [{
                formDef: configurationAzureForm,
                id: 'auth-azure-form',
                name: 'azure'
            }, {
                formDef: configurationGithubForm,
                id: 'auth-github-form',
                name: 'github'
            }, {
                formDef: configurationGithubOrgForm,
                id: 'auth-github-org-form',
                name: 'github_org'
            }, {
                formDef: configurationGithubTeamForm,
                id: 'auth-github-team-form',
                name: 'github_team'
            }, {
                formDef: configurationGoogleForm,
                id: 'auth-google-form',
                name: 'google_oauth'
            }, {
                formDef: configurationLdapForm,
                id: 'auth-ldap-form',
                name: 'ldap'
            }, {
                formDef: configurationRadiusForm,
                id: 'auth-radius-form',
                name: 'radius'
            }, {
                formDef: configurationTacacsForm,
                id: 'auth-tacacs-form',
                name: 'tacacs'
            }, {
                formDef: configurationSamlForm,
                id: 'auth-saml-form',
                name: 'saml'
            }, ];

        var forms = _.pluck(authForms, 'formDef');
        _.each(forms, function(form) {
            var keys = _.keys(form.fields);
            _.each(keys, function(key) {
                if($scope.$parent.configDataResolve[key].type === 'choice') {
                    // Create options for dropdowns
                    var optionsGroup = key + '_options';
                    $scope.$parent[optionsGroup] = [];
                    _.each($scope.$parent.configDataResolve[key].choices, function(choice){
                        $scope.$parent[optionsGroup].push({
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

        function startCodeMirrors(key){
            var form = _.find(authForms, function(f){
               return f.name === $scope.authVm.activeAuthForm;
            });

            if(!key){
                // Attach codemirror to fields that need it
                _.each(form.formDef.fields, function(field) {
                    // Codemirror balks at empty values so give it one
                    if($scope.$parent[field.name] === null && field.codeMirror) {
                      $scope.$parent[field.name] = '{}';
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
                   scope: $scope.$parent,
                   variable: name,
                   parse_variable: 'parseType',
                   field_id: form.formDef.name + '_' + name
                 });
                 $scope.parseTypeChange('parseType', name);
            }
        }

        function addFieldInfo(form, key) {
            _.extend(form.fields[key], {
                awPopOver: ($scope.$parent.configDataResolve[key].defined_in_file) ?
                    null: $scope.$parent.configDataResolve[key].help_text,
                label: $scope.$parent.configDataResolve[key].label,
                name: key,
                toggleSource: key,
                dataPlacement: 'top',
                placeholder: ConfigurationUtils.formatPlaceholder($scope.$parent.configDataResolve[key].placeholder, key) || null,
                dataTitle: $scope.$parent.configDataResolve[key].label,
                required: $scope.$parent.configDataResolve[key].required,
                ngDisabled: $rootScope.user_is_system_auditor,
                disabled: $scope.$parent.configDataResolve[key].disabled || null,
                readonly: $scope.$parent.configDataResolve[key].readonly || null,
                definedInFile: $scope.$parent.configDataResolve[key].defined_in_file || null
            });
        }

        $scope.$parent.parseType = 'json';

        _.each(authForms, function(form) {
            // Generate the forms
            generator.inject(form.formDef, {
                id: form.id,
                mode: 'edit',
                scope: $scope.$parent,
                related: true,
                noPanel: true
            });
        });

        // Flag to avoid re-rendering and breaking Select2 dropdowns on tab switching
        var dropdownRendered = false;

        function populateLDAPGroupType(flag){
            if($scope.$parent.AUTH_LDAP_GROUP_TYPE !== null) {
                $scope.$parent.AUTH_LDAP_GROUP_TYPE = _.find($scope.$parent.AUTH_LDAP_GROUP_TYPE_options, { value: $scope.$parent.AUTH_LDAP_GROUP_TYPE });
            }

            if(flag !== undefined){
                dropdownRendered = flag;
            }

            if(!dropdownRendered) {
                dropdownRendered = true;
                CreateSelect2({
                    element: '#configuration_ldap_template_AUTH_LDAP_GROUP_TYPE',
                    multiple: false,
                    placeholder: i18n._('Select group types'),
                });
            }
        }

        function populateTacacsProtocol(flag){
            if($scope.$parent.TACACSPLUS_AUTH_PROTOCOL !== null) {
                $scope.$parent.TACACSPLUS_AUTH_PROTOCOL = _.find($scope.$parent.TACACSPLUS_AUTH_PROTOCOL_options, { value: $scope.$parent.TACACSPLUS_AUTH_PROTOCOL });
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

        $scope.$on('AUTH_LDAP_GROUP_TYPE_populated', function(e, data, flag) {
            populateLDAPGroupType(flag);
        });

        $scope.$on('TACACSPLUS_AUTH_PROTOCOL_populated', function(e, data, flag) {
            populateTacacsProtocol(flag);
        });

        $scope.$on('$locationChangeStart', (event, url) => {
            let parts = url.split('/');
            let tab = parts[parts.length - 1];

            if (tab === 'auth') {
                startCodeMirrors();
                codeInputInitialized = true;
            }
        });

        $scope.$on('populated', function() {
            let tab = $stateParams.currentTab;

            if (tab === 'auth') {
                startCodeMirrors();
                codeInputInitialized = true;
            }

            populateLDAPGroupType(false);
            populateTacacsProtocol(false);
        });

        $scope.$on('codeMirror_populated', function() {
            let tab = $stateParams.currentTab;
            if (tab === 'auth') {
                startCodeMirrors();
                codeInputInitialized = true;
            }
        });


        angular.extend(authVm, {
            activeForm: activeForm,
            activeAuthForm: activeAuthForm,
            authForms: authForms,
            dropdownOptions: dropdownOptions,
            dropdownValue: dropdownValue
        });
    }
];
