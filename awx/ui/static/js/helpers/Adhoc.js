/*********************************************
 *  Copyright (c) 2015 AnsibleWorks, Inc.
 *
 *  AdhocHelper
 *
 *  Routines shared by adhoc related controllers:
 */
/**
 * @ngdoc function
 * @name helpers.function:Adhoc
 * @description routines shared by adhoc related controllers
 * AdhocRun is currently only used for _relaunching_ an adhoc command
 * from the Jobs page.
 * TODO: once the API endpoint is figured out for running an adhoc command
 * from the form is figured out, the rest work should probably be excised from
 * the controller and moved into here.  See the todo statements in the
 * controller for more information about this.
 */

export default
    angular.module('AdhocHelper', ['RestServices', 'Utilities',
        'CredentialFormDefinition', 'CredentialsListDefinition', 'LookUpHelper',
        'JobSubmissionHelper', 'JobTemplateFormDefinition', 'ModalDialog',
        'FormGenerator', 'JobVarsPromptFormDefinition'])

    /**
    * @ngdoc method
    * @name helpers.function:JobSubmission#AdhocRun
    * @methodOf helpers.function:JobSubmission
    * @description The adhoc Run function is run when the user clicks the relaunch button
    *
    */
    // Submit request to run an adhoc comamand
    .factory('AdhocRun', ['$location','$routeParams', 'LaunchJob',
        'PromptForPasswords', 'Rest', 'GetBasePath', 'Alert', 'ProcessErrors',
        'Wait', 'Empty', 'PromptForCredential', 'PromptForVars',
        'PromptForSurvey' , 'CreateLaunchDialog',
    function ($location, $routeParams, LaunchJob, PromptForPasswords,
        Rest, GetBasePath, Alert, ProcessErrors, Wait, Empty,
        PromptForCredential, PromptForVars, PromptForSurvey,
        CreateLaunchDialog) {
        return function (params) {
            var id = params.project_id,
                scope = params.scope.$new(),
                new_job_id,
                launch_url,
                html,
                url;

            // this is used to cancel a running adhoc command from
            // the jobs page
            if (scope.removeCancelJob) {
                scope.removeCancelJob();
            }
            scope.removeCancelJob = scope.$on('CancelJob', function() {
                // Delete the job
                Wait('start');
                Rest.setUrl(GetBasePath('ad_hoc_commands') + new_job_id + '/');
                Rest.destroy()
                    .success(function() {
                        Wait('stop');
                    })
                    .error(function (data, status) {
                        ProcessErrors(scope, data, status,
                          null, { hdr: 'Error!',
                              msg: 'Call to ' + url
                                + ' failed. DELETE returned status: '
                                + status });
                    });
            });

            if (scope.removeAdhocLaunchFinished) {
                scope.removeAdhocLaunchFinished();
            }
            scope.removeAdhocLaunchFinished = scope.$on('AdhocLaunchFinished',
                function(e, data) {
                    $location.path('/ad_hoc_commands/' + data.id);
                });

            if (scope.removeStartAdhocRun) {
                scope.removeStartAdhocRun();
            }

            scope.removeStartAdhocRun = scope.$on('StartAdhocRun', function() {
                LaunchJob({
                    scope: scope,
                    url: url,
                    callback: 'AdhocLaunchFinished' // send to the adhoc
                    // standard out page
                });
            });

            //  start routine only if passwords need to be prompted
            if (scope.removeCreateLaunchDialog) {
                scope.removeCreateLaunchDialog();
            }
            scope.removeCreateLaunchDialog = scope.$on('CreateLaunchDialog',
                function(e, html, url) {
                    CreateLaunchDialog({
                        scope: scope,
                        html: html,
                        url: url,
                        callback: 'StartAdhocRun'
                    });
                });

            if (scope.removePromptForPasswords) {
                scope.removePromptForPasswords();
            }
            scope.removePromptForPasswords = scope.$on('PromptForPasswords',
                function(e, passwords_needed_to_start,html, url) {
                    PromptForPasswords({
                        scope: scope,
                        passwords: passwords_needed_to_start,
                        callback: 'CreateLaunchDialog',
                        html: html,
                        url: url
                    });
            }); // end password prompting routine

            // start the adhoc relaunch routine
            Wait('start');
            url = GetBasePath('ad_hoc_commands') + id + '/relaunch/';
            Rest.setUrl(url);
            Rest.get()
                .success(function (data) {
                    var new_job_id = data.id,
                        launch_url = url;

                    scope.passwords_needed_to_start = data.passwords_needed_to_start;
                    if (!Empty(data.passwords_needed_to_start) &&
                        data.passwords_needed_to_start.length > 0) {
                        // go through the password prompt routine before
                        // starting the adhoc run
                        scope.$emit('PromptForPasswords', data.passwords_needed_to_start, html, url);
                    }
                    else {
                        // no prompting of passwords needed
                        scope.$emit('StartAdhocRun');
                    }
                })
                .error(function (data, status) {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                    msg: 'Failed to get job template details. GET returned status: ' + status });
                });
        };
    }]);
