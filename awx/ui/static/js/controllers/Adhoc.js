/*************************************************
 * Copyright (c) 2015 AnsibleWorks, Inc.
 *
 *  Adhoc.js
 *
 *  Controller functions for the Adhoc model.
 *
 */
/**
 * @ngdoc function
 * @name controllers.function:Adhoc
 * @description This controller controls the adhoc form creation, command launching and navigating to standard out after command has been succesfully ran.
*/
export function AdhocCtrl($scope, $rootScope, $location, $routeParams,
    CheckPasswords, PromptForPasswords, CreateLaunchDialog, AdhocForm, GenerateForm, Rest, ProcessErrors, ClearScope,
    GetBasePath, GetChoices, KindChange, LookUpInit, CredentialList, Empty,
    Wait) {

    ClearScope();

    var url = GetBasePath('inventory') + $routeParams.inventory_id +
        '/ad_hoc_commands/',
        generator = GenerateForm,
        form = AdhocForm,
        master = {},
        id = $routeParams.inventory_id,
        choicesReadyCount = 0;

    // inject the adhoc command form
    generator.inject(form, { mode: 'edit', related: true, scope: $scope });
    generator.reset();

    // BEGIN: populate scope with the things needed to make the adhoc form
    // display
    Wait('start');
    $scope.id = id;
    $scope.argsPopOver = "<p>These arguments are used with the" +
        " specified module.</p>";
    // fix arguments help popover based on the module selected
    $scope.moduleChange = function () {
        // NOTE: for selenium testing link -
        // link will be displayed with id adhoc_module_arguments_docs_link
        // only when a module is selected
        if ($scope.module_name) {
            // give the docs for the selected module
            $scope.argsPopOver = "<p>These arguments are used with the" +
                " specified module. You can find information about the " +
                $scope.module_name.value +
                " <a id=\"adhoc_module_arguments_docs_link_for_module_" +
                $scope.module_name.value +
                "\"" +
                " href=\"http://docs.ansible.com/" + $scope.module_name.value +
                "_module.html\" target=\"_blank\">here</a>.</p>";
        } else {
            // no module selected
            $scope.argsPopOver = "<p>These arguments are used with the" +
                " specified module.</p>";
        }
    };

    // pre-populate hostPatterns from the inventory page and
    // delete the value off of rootScope
    $scope.limit = $rootScope.hostPatterns || "all";
    $scope.providedHostPatterns = $scope.limit;
    delete $rootScope.hostPatterns;

    if ($scope.removeLookUpInitialize) {
        $scope.removeLookUpInitialize();
    }
    $scope.removeLookUpInitialize = $scope.$on('lookUpInitialize', function () {
        LookUpInit({
            scope: $scope,
            form: form,
            current_item: (!Empty($scope.credential_id)) ? $scope.credential_id : null,
            list: CredentialList,
            field: 'credential',
            input_type: 'radio'
        });

        Wait('stop'); // END: form population
    });

    if ($scope.removeChoicesReady) {
        $scope.removeChoicesReady();
    }
    $scope.removeChoicesReady = $scope.$on('choicesReadyAdhoc', function () {
        choicesReadyCount++;

        if (choicesReadyCount === 2) {
            // this sets the default option as specified by the controller.
            $scope.verbosity = $scope.adhoc_verbosity_options[$scope.verbosity_field.default];
            $scope.$emit('lookUpInitialize');
        }
    });

    // setup Machine Credential lookup
    GetChoices({
        scope: $scope,
        url: url,
        field: 'module_name',
        variable: 'adhoc_module_options',
        callback: 'choicesReadyAdhoc'
    });

    // setup verbosity options lookup
    GetChoices({
        scope: $scope,
        url: url,
        field: 'verbosity',
        variable: 'adhoc_verbosity_options',
        callback: 'choicesReadyAdhoc'
    });

    // launch the job with the provided form data
    $scope.launchJob = function () {
        var fld, data={}, html;

        html = '<form class="ng-valid ng-valid-required" name="job_launch_form"' +
            'id="job_launch_form" autocomplete="off" nonvalidate>';

        // stub the payload with defaults from DRF
        data = {
            "job_type": "run",
            "limit": "",
            "credential": null,
            "module_name": "command",
            "module_args": "",
            "forks": 0,
            "verbosity": 0,
            "privilege_escalation": ""
        };

        generator.clearApiErrors();

        // populate data with the relevant form values
        for (fld in form.fields) {
            if (form.fields[fld].type === 'select') {
                data[fld] = $scope[fld].value;
            } else {
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
                    data[$scope.passwords[password]] = $scope[$scope.passwords[password]];
                }
                // Launch the adhoc job
                Rest.setUrl(GetBasePath('inventory') +
                    $routeParams.inventory_id + '/ad_hoc_commands/');
                Rest.post(data)
                    .success(function (data) {
                         Wait('stop');
                         $location.path("/ad_hoc_commands/" + data.id);
                    })
                    .error(function (data, status) {
                        ProcessErrors($scope, data, status, form, { hdr: 'Error!',
                            msg: 'Failed to launch adhoc command. POST returned ' +
                                'status: ' + status });
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
        $scope.removePromptForPasswords = $scope.$on('PromptForPasswords', function(e, passwords_needed_to_start,html, url) {
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
        $scope.removeContinueCred = $scope.$on('ContinueCred', function(e, passwords) {
            if(passwords.length>0){
                $scope.passwords_needed_to_start = passwords;
                // only go through the password prompting steps if there are
                // passwords to prompt for
                $scope.$emit('PromptForPasswords', passwords, html, url);
            } else {
                // if not, go straight to trying to run the job.
                $scope.$emit('StartAdhocRun', url);
            }
        });

        //  start adhoc launching routine
        CheckPasswords({
            scope: $scope,
            credential: $scope.credential,
            callback: 'ContinueCred'
        });

        // // Launch the adhoc job
        // Rest.setUrl(url);
        // Rest.post(data)
        //     .success(function (data) {
        //          Wait('stop');
        //          $location.path("/ad_hoc_commands/" + data.id);
        //     })
        //     .error(function (data, status) {
        //         ProcessErrors($scope, data, status, form, { hdr: 'Error!',
        //             msg: 'Failed to launch adhoc command. POST returned status: ' +
        //                 status });
        //         // TODO: still need to implement popping up a password prompt
        //         // if the credential requires it.  The way that the current end-
        //         // point works is that I find out if I need to ask for a
        //         // password from POST, thus I get an error response.
        //     });
    };

    // Remove all data input into the form
    $scope.formReset = function () {
        generator.reset();
        for (var fld in master) {
            $scope[fld] = master[fld];
        }
        $scope.limit = $scope.providedHostPatterns;
        KindChange({ scope: $scope, form: form, reset: false });
    };
}

AdhocCtrl.$inject = ['$scope', '$rootScope', '$location', '$routeParams',
    'CheckPasswords', 'PromptForPasswords', 'CreateLaunchDialog', 'AdhocForm',
    'GenerateForm', 'Rest', 'ProcessErrors', 'ClearScope', 'GetBasePath',
    'GetChoices', 'KindChange', 'LookUpInit', 'CredentialList', 'Empty', 'Wait'];
