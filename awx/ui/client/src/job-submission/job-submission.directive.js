/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import jobSubmissionController from './job-submission.controller';

export default [ 'templateUrl', 'CreateDialog', 'Wait', 'CreateSelect2', 'ParseTypeChange', 'GetSurveyQuestions', 'i18n', 'credentialTypesLookup', '$transitions',
    function(templateUrl, CreateDialog, Wait, CreateSelect2, ParseTypeChange, GetSurveyQuestions, i18n, credentialTypesLookup, $transitions) {
    return {
        scope: {
            submitJobId: '=',
            submitJobType: '@',
            submitJobRelaunch: '=',
            relaunchHostType: '@'
        },
        templateUrl: templateUrl('job-submission/job-submission'),
        controller: jobSubmissionController,
        restrict: 'E',
        link: function(scope) {

            scope.openLaunchModal = function() {
                if (scope.removeLaunchJobModalReady) {
                    scope.removeLaunchJobModalReady();
                }
                scope.removeLaunchJobModalReady = scope.$on('LaunchJobModalReady', function() {
                    credentialTypesLookup()
                        .then(kinds => {
                            if(scope.ask_credential_on_launch) {
                                scope.credentialKind = "" + kinds.ssh;
                                scope.includeCredentialList = true;
                            }
                        });

                    // Go get the list/survey data that we need from the server
                    if(scope.ask_inventory_on_launch) {
                        scope.includeInventoryList = true;
                    }
                    if(scope.survey_enabled) {
                        GetSurveyQuestions({
                            scope: scope,
                            id: scope.submitJobId,
                            submitJobType: scope.submitJobType
                        });

                    }

                    $('#job-launch-modal').dialog('open');

                    // select2-ify the job type dropdown
                    CreateSelect2({
                        element: '#job_launch_job_type',
                        multiple: false
                    });

                    CreateSelect2({
                        element: '#job_launch_verbosity',
                        multiple: false
                    });

                    CreateSelect2({
                        element: `#job-launch-credential-kind-select`,
                        multiple: false,
                        placeholder: i18n._('Select a credential')
                    });

                    CreateSelect2({
                        element: '#job_launch_job_tags',
                        multiple: true,
                        addNew: true
                    });

                    CreateSelect2({
                        element: '#job_launch_skip_tags',
                        multiple: true,
                        addNew: true
                    });

                    if(scope.step === 'otherprompts' && scope.ask_variables_on_launch) {
                        ParseTypeChange({
                            scope: scope,
                            variable: 'jobLaunchVariables',
                            field_id: 'job_launch_variables'
                        });

                        scope.extra_vars_code_mirror_loaded = true;
                    }

                });

                CreateDialog({
                    id: 'job-launch-modal',
                    scope: scope,
                    width: 800,
                    minWidth: 400,
                    draggable: false,
                    dialogClass: 'JobSubmission-dialog',
                    onOpen: function() {
                        Wait('stop');
                    },
                    callback: 'LaunchJobModalReady'
                });
            };

            scope.clearDialog = function() {
                // Destroy the dialog
                if($("#job-launch-modal").hasClass('ui-dialog-content')) {
                    $('#job-launch-modal').dialog('destroy');
                }
                // Remove the directive from the page
                $('#content-container').find('submit-job').remove();

                // Clear out the scope (we'll create a new scope the next time
                // job launch is called)
                scope.$destroy();
            };

            // This function is used to hide/show the contents of a password
            // within a form
            scope.togglePassword = function(id) {
                var buttonId = id + "_show_input_button",
                inputId = id,
                buttonInnerHTML = $(buttonId).html();
                if (buttonInnerHTML.indexOf("Show") > -1) {
                    $(buttonId).html("Hide");
                    $(inputId).attr("type", "text");
                } else {
                    $(buttonId).html("Show");
                    $(inputId).attr("type", "password");
                }
            };

            $transitions.onStart({}, function() {
                scope.$evalAsync(function( scope ) {
                    scope.clearDialog();
                });
            });

            scope.init();

        }
    };
}];
