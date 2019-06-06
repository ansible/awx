/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/**
 * @ngdoc function
 * @name controllers.function:Adhoc
 * @description This controller controls the adhoc form creation, command launching and navigating to standard out after command has been succesfully ran.
*/
function adhocController($q, $scope, $stateParams,
    $state, CheckPasswords, PromptForPasswords, CreateLaunchDialog, CreateSelect2, adhocForm,
    GenerateForm, Rest, ProcessErrors, GetBasePath, GetChoices,
    KindChange, Wait, ParseTypeChange, machineCredentialType) {

    // this is done so that we can access private functions for testing, but
    // we don't want to populate the "public" scope with these internal
    // functions
    var privateFn = {};
    this.privateFn = privateFn;

    var id = $stateParams.inventory_id ? $stateParams.inventory_id : $stateParams.smartinventory_id,
        hostPattern = $stateParams.pattern;

    // note: put any urls that the controller will use in here!!!!
    privateFn.setAvailableUrls = function() {
        return {
            adhocUrl: GetBasePath('inventory') + id + '/ad_hoc_commands/',
            inventoryUrl: GetBasePath('inventory') + id + '/',
            machineCredentialUrl: GetBasePath('credentials') + '?credential_type__namespace=ssh'
        };
    };

    var urls = privateFn.setAvailableUrls();

    // set the default options for the selects of the adhoc form
    privateFn.setFieldDefaults = function(verbosity_options, forks_default) {
        var verbosity;
        for (verbosity in verbosity_options) {
            if (verbosity_options[verbosity].isDefault) {
                $scope.verbosity = verbosity_options[verbosity];
            }
        }
        if (forks_default !== 0) {
            $("#forks-number").spinner("value", forks_default);
            $scope.forks = forks_default;
        }
    };

    // set when "working" starts and stops
    privateFn.setLoadingStartStop = function() {
        var asyncHelper = {},
            formReadyPromise = 0;

        Wait('start');

        if (asyncHelper.removeChoicesReady) {
            asyncHelper.removeChoicesReady();
        }
        asyncHelper.removeChoicesReady = $scope.$on('adhocFormReady',
                                                    isFormDone);

        // check to see if all requests have completed
        function isFormDone() {
            formReadyPromise++;

            if (formReadyPromise === 2) {
                privateFn.setFieldDefaults($scope.adhoc_verbosity_options,
                    $scope.forks_field.default);

                CreateSelect2({
                    element: '#adhoc_module_name',
                    multiple: false
                });

                CreateSelect2({
                    element: '#adhoc_verbosity',
                    multiple: false
                });

                Wait('stop');
            }
        }
    };

    // set the arguments help to watch on change of the module
    privateFn.instantiateArgumentHelp = function() {
        $scope.$watch('module_name', function(val) {
            if (val) {
                // give the docs for the selected module in the popover
                $scope.argsPopOver = '<p>These arguments are used with the ' +
                    'specified module. You can find information about the ' +
                    val.value + ' module <a ' +
                    'id=\"adhoc_module_arguments_docs_link_for_module_' +
                    val.value + '\" href=\"http://docs.ansible.com/' +
                    val.value + '_module.html\" ' +
                    'target=\"_blank\">here</a>.</p>';
            } else {
                // no module selected
                $scope.argsPopOver = "<p>These arguments are used with the" +
                    " specified module.</p>";
            }
        }, true);

        // initially set to the same as no module selected
        $scope.argsPopOver = "<p>These arguments are used with the " +
            "specified module.</p>";
    };

    // pre-populate host patterns from the inventory page and
    // delete the value off of rootScope
    privateFn.instantiateHostPatterns = function(hostPattern) {
        $scope.limit = hostPattern;
        $scope.providedHostPatterns = $scope.limit;
    };

    // call helpers to initialize lookup and select fields through get
    // requests
    privateFn.initializeFields = function(machineCredentialUrl, adhocUrl) {

        // setup module name select
        GetChoices({
            scope: $scope,
            url: adhocUrl,
            field: 'module_name',
            variable: 'adhoc_module_options',
            callback: 'adhocFormReady'
        });

        // setup verbosity options select
        GetChoices({
            scope: $scope,
            url: adhocUrl,
            field: 'verbosity',
            variable: 'adhoc_verbosity_options',
            callback: 'adhocFormReady'
        });
    };

    // instantiate all variables on scope for display in the partial
    privateFn.initializeForm = function(id, urls, hostPattern) {
        // inject the adhoc command form
        GenerateForm.inject(adhocForm,
            { mode: 'add', related: true, scope: $scope });

        // set when "working" starts and stops
        privateFn.setLoadingStartStop();

        // put the inventory id on scope for the partial to use
        $scope.inv_id = id;

        // set the arguments help to watch on change of the module
        privateFn.instantiateArgumentHelp();

        // pre-populate host patterns from the inventory page and
        // delete the value off of rootScope
        privateFn.instantiateHostPatterns(hostPattern);

        privateFn.initializeFields(urls.machineCredentialUrl, urls.adhocUrl);
    };

    privateFn.initializeForm(id, urls, hostPattern);

    // init codemirror
    $scope.extra_vars = '---';
    $scope.parseType = 'yaml';
    $scope.envParseType = 'yaml';
    ParseTypeChange({ scope: $scope, field_id: 'adhoc_extra_vars' , variable: "extra_vars"});

    $scope.toggleForm = function(key) {
        $scope[key] = !$scope[key];
    };

    $scope.formCancel = function(){
        $state.go('^');
    };

    // remove all data input into the form and reset the form back to defaults
    $scope.formReset = function () {
        GenerateForm.reset();

        // pre-populate host patterns from the inventory page and
        // delete the value off of rootScope
        privateFn.instantiateHostPatterns($scope.providedHostPatterns);

        KindChange({ scope: $scope, form: adhocForm, reset: false });

        // set the default options for the selects of the adhoc form
        privateFn.setFieldDefaults($scope.adhoc_verbosity_options,
            $scope.forks_default);
    };

    // launch the job with the provided form data
    $scope.launchJob = function () {
        var adhocUrl = GetBasePath('inventory') + id +
        '/ad_hoc_commands/', fld, data={}, html;

        html = '<form class="ng-valid ng-valid-required" ' +
            'name="job_launch_form" id="job_launch_form" autocomplete="off" ' +
            'nonvalidate>';

        // stub the payload with defaults from DRF
        data = {
            "job_type": "run",
            "limit": "",
            "credential": "",
            "module_name": "command",
            "module_args": "",
            "forks": 0,
            "verbosity": 0,
            "extra_vars": "",
            "privilege_escalation": ""
        };

        GenerateForm.clearApiErrors($scope);

        // populate data with the relevant form values
        for (fld in adhocForm.fields) {
            if (adhocForm.fields[fld].type === 'select') {
                data[fld] = $scope[fld].value;
            } else if ($scope[fld]) {
                data[fld] = $scope[fld];
            }
        }

        Wait('start');

        if ($scope.removeStartAdhocRun) {
          $scope.removeStartAdhocRun();
        }
        $scope.removeStartAdhocRun = $scope.$on('StartAdhocRun', function() {
            var password;
            for (password in $scope.passwords) {
                data[$scope.passwords[password]] = $scope[
                    $scope.passwords[password]
                ];
            }
            // Launch the adhoc job
            Rest.setUrl(GetBasePath('inventory') + id + '/ad_hoc_commands/');
            Rest.post(data)
                .then(({data}) => {
                     Wait('stop');
                     $state.go('output', {id: data.id, type: 'command'});
                })
                .catch(({data, status}) => {
                    ProcessErrors($scope, data, status, adhocForm, {
                        hdr: 'Error!',
                        msg: 'Failed to launch adhoc command. POST ' +
                            'returned status: ' + status });
                });
        });

        if ($scope.removeCreateLaunchDialog) {
            $scope.removeCreateLaunchDialog();
        }
        $scope.removeCreateLaunchDialog = $scope.$on('CreateLaunchDialog',
            function(e, html, url) {
                CreateLaunchDialog({
                    scope: $scope,
                    html: html,
                    url: url,
                    callback: 'StartAdhocRun'
                });
            });

        if ($scope.removePromptForPasswords) {
          $scope.removePromptForPasswords();
        }
        $scope.removePromptForPasswords = $scope.$on('PromptForPasswords',
            function(e, passwords_needed_to_start,html, url) {
                PromptForPasswords({ scope: $scope,
                passwords: passwords_needed_to_start,
                callback: 'CreateLaunchDialog',
                html: html,
                url: url
            });
        });

        if ($scope.removeContinueCred) {
          $scope.removeContinueCred();
        }
        $scope.removeContinueCred = $scope.$on('ContinueCred', function(e,
            passwords) {
            if(passwords.length>0){
                $scope.passwords_needed_to_start = passwords;
                // only go through the password prompting steps if there are
                // passwords to prompt for
                $scope.$emit('PromptForPasswords', passwords, html, adhocUrl);
            } else {
                // if not, go straight to trying to run the job.
                $scope.$emit('StartAdhocRun', adhocUrl);
            }
        });

        //  start adhoc launching routine
        CheckPasswords({
            scope: $scope,
            credential: $scope.credential,
            callback: 'ContinueCred'
        });
    };

    $scope.lookupCredential = function(){
        $state.go('.credential', {
            credential_search: {
                credential_type: machineCredentialType,
                page_size: '5',
                page: '1'
            }
        });
    };

}

export default ['$q', '$scope', '$stateParams',
    '$state', 'CheckPasswords', 'PromptForPasswords', 'CreateLaunchDialog', 'CreateSelect2',
     'adhocForm', 'GenerateForm', 'Rest', 'ProcessErrors', 'GetBasePath',
    'GetChoices', 'KindChange', 'Wait', 'ParseTypeChange', 'machineCredentialType',
    adhocController];
