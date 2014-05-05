/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  JobSubmission.js
 *
 */

'use strict';

angular.module('JobSubmissionHelper', [ 'RestServices', 'Utilities', 'CredentialFormDefinition', 'CredentialsListDefinition',
    'LookUpHelper', 'JobSubmissionHelper', 'JobTemplateFormDefinition', 'ModalDialog'])

.factory('LaunchJob', ['Rest', 'Wait', 'ProcessErrors', function(Rest, Wait, ProcessErrors) {
    return function(params) {
        var scope = params.scope,
            passwords = params.passwords || {},
            callback = params.callback || 'JobLaunched',
            url = params.url;
        
        Wait('start');
        Rest.setUrl(url);
        Rest.post(passwords)
            .success(function(data) {
                scope.$emit(callback, data);
            })
            .error(function (data, status) {
                ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                    msg: 'Attempt to start job at ' + url + ' failed. POST returned: ' + status });
            });
    };
}])

.factory('PromptForCredential', ['$location', 'Wait', 'GetBasePath', 'LookUpInit', 'JobTemplateForm', 'CredentialList', 'Rest', 'Prompt', 'ProcessErrors',
function($location, Wait, GetBasePath, LookUpInit, JobTemplateForm, CredentialList, Rest, Prompt, ProcessErrors) {
    return function(params) {
        
        var scope = params.scope,
            callback = params.callback || 'CredentialReady',
            selectionMade;
        
        Wait('stop');
        scope.credential = '';

        if (scope.removeShowLookupDialog) {
            scope.removeShowLookupDialog();
        }
        scope.removeShowLookupDialog = scope.$on('ShowLookupDialog', function() {
            selectionMade = function () {
                scope.$emit(callback, scope.credential);
            };
            
            LookUpInit({
                url: GetBasePath('credentials') + '?kind=ssh',
                scope: scope,
                form: JobTemplateForm(),
                current_item: null,
                list: CredentialList,
                field: 'credential',
                hdr: 'Credential Required',
                instructions: "Launching this job requires a machine credential. Please select your machine credential now or Cancel to quit.",
                postAction: selectionMade
            });
            scope.lookUpCredential();
        });

        if (scope.removeAlertNoCredentials) {
            scope.removeAlertNoCredentials();
        }
        scope.removeAlertNoCredentials = scope.$on('AlertNoCredentials', function() {
            var action = function () {
                $('#prompt-modal').modal('hide');
                $location.url('/credentials/add');
            };

            Prompt({
                hdr: 'Machine Credential Required',
                body: "<div class=\"alert alert-info\">There are no machine credentials defined in Tower. Launching this job requires a machine credential. " +
                    "Create one now?",
                action: action
            });
        });

        Rest.setUrl(GetBasePath('credentials') + '?kind=ssh');
        Rest.get()
            .success(function(data) {
                if (data.results.length > 0) {
                    scope.$emit('ShowLookupDialog');
                }
                else {
                    scope.$emit('AlertNoCredentials');
                }
            })
            .error(function(data,status) {
                ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                    msg: 'Checking for machine credentials failed. GET returned: ' + status });
            });
    };
}])

.factory('PromptForPasswords', ['$compile', 'Wait', 'Alert', 'CredentialForm', 'CreateDialog',
    function($compile, Wait, Alert, CredentialForm, CreateDialog) {
        return function(params) {
            var parent_scope = params.scope,
                passwords = params.passwords,
                callback = params.callback || 'PasswordsAccepted',
                form = CredentialForm,
                acceptedPasswords = {},
                scope = parent_scope.$new(),
                e, buttons;
                
            Wait('stop');
            
            function buildHtml() {
                var fld, field, html;
                html = "";
                html += "<div class=\"alert alert-info\">Launching this job requires the passwords listed below. Enter and confirm each password before continuing.</div>\n";
                html += "<form name=\"password_form\" novalidate>\n";
                
                passwords.forEach(function(password) {
                    // Prompt for password
                    field = form.fields[password];
                    fld = password;
                    scope[fld] = '';
                    html += "<div class=\"form-group\">\n";
                    html += "<label for=\"" + fld + "\">* " + field.label + "</label>\n";
                    html += "<input type=\"password\" ";
                    html += "ng-model=\"" + fld + '" ';
                    html += 'name="' + fld + '" ';
                    html += "class=\"password-field form-control input-sm\" ";
                    html += (field.associated) ? "ng-change=\"clearPWConfirm('" + field.associated + "')\" " : "";
                    html += "required ";
                    html += " >";
                    // Add error messages
                    html += "<div class=\"error\" ng-show=\"password_form." + fld + ".$dirty && " +
                        "password_form." + fld + ".$error.required\">A value is required!</div>\n";
                    html += "<div class=\"error api-error\" ng-bind=\"" + fld + "_api_error\"></div>\n";
                    html += "</div>\n";

                    // Add the related confirm field
                    if (field.associated) {
                        fld = field.associated;
                        field = form.fields[field.associated];
                        scope[fld] = '';
                        html += "<div class=\"form-group\">\n";
                        html += "<label for=\"" + fld + "\">* " + field.label + "</label>\n";
                        html += "<input type=\"password\" ";
                        html += "ng-model=\"" + fld + '" ';
                        html += 'name="' + fld + '" ';
                        html += "class=\"form-control input-sm\" ";
                        html += "ng-change=\"checkStatus()\" ";
                        html += "required ";
                        html += (field.awPassMatch) ? "awpassmatch=\"" + field.associated + "\" " : "";
                        html += "/>";
                        // Add error messages
                        html += "<div class=\"error\" ng-show=\"password_form." + fld + ".$dirty && " +
                            "password_form." + fld + ".$error.required\">A value is required!</span>\n";
                        html += (field.awPassMatch) ? "<span class=\"error\" ng-show=\"password_form." + fld +
                            ".$error.awpassmatch\">Must match Password value</div>\n" : "";
                        html += "<div class=\"error api-error\" ng-bind=\"" + fld + "_api_error\"></div>\n";
                        html += "</div>\n";
                    }
                });
                html += "</form>\n";
                return html;
            }

            $('#password-modal').empty().html(buildHtml);
            e = angular.element(document.getElementById('password-modal'));
            $compile(e)(scope);

            buttons = [{
                label: "Cancel",
                onClick: function() {
                    scope.passwordCancel();
                },
                icon: "fa-times",
                "class": "btn btn-default",
                "id": "password-cancel-button"
            },{
                label: "Continue",
                onClick: function() {
                    scope.passwordAccept();
                },
                icon: "fa-check",
                "class": "btn btn-primary",
                "id": "password-accept-button"
            }];

            CreateDialog({
                id: 'password-modal',
                scope: scope,
                buttons: buttons,
                width: 600,
                height: (passwords.length > 1) ? 700 : 500,
                minWidth: 500,
                title: 'Passwords Required',
                callback: 'DialogReady'
            });

            if (scope.removeDialogReady) {
                scope.removeDialogReady();
            }
            scope.removeDialogReady = scope.$on('DialogReady', function() {
                $('#password-modal').dialog('open');
                $('#password-accept-button').attr({ "disabled": "disabled" });
            });
            
            scope.passwordAccept = function() {
                if (!scope.password_form.$invalid) {
                    passwords.forEach(function(password) {
                        acceptedPasswords[password] = scope[password];
                    });
                    $('#password-modal').dialog('close');
                    parent_scope.$emit(callback, acceptedPasswords);
                }
            };

            scope.passwordCancel = function() {
                $('#password-modal').dialog('close');
                Alert('Missing Password', 'Required password(s) not provided. Your request will not be submitted.', 'alert-info');
                parent_scope.$emit('PasswordsCanceled');
                scope.$destroy();
            };

            // Password change
            scope.clearPWConfirm = function (fld) {
                // If password value changes, make sure password_confirm must be re-entered
                scope[fld] = '';
                scope.password_form[fld].$setValidity('awpassmatch', false);
                scope.checkStatus();
            };

            scope.checkStatus = function() {
                if (!scope.password_form.$invalid) {
                    $('#password-accept-button').removeAttr('disabled');
                }
                else {
                    $('#password-accept-button').attr({ "disabled": "disabled" });
                }
            };
        };
    }])

// Submit request to run a playbook
.factory('PlaybookRun', ['$location','$routeParams', 'LaunchJob', 'PromptForPasswords', 'Rest', 'GetBasePath', 'ProcessErrors', 'Wait', 'Empty', 'PromptForCredential',
    function ($location, $routeParams, LaunchJob, PromptForPasswords, Rest, GetBasePath, ProcessErrors, Wait, Empty, PromptForCredential) {
        return function (params) {
            var scope = params.scope,
                id = params.id,
                base = $location.path().replace(/^\//, '').split('/')[0],
                url, job_template, new_job_id, launch_url;

            if (!Empty($routeParams.template_id)) {
                // launching a job from job_template detail page
                url = GetBasePath('jobs') + id + '/';
            }
            else {
                url = GetBasePath(base) + id + '/';
            }

            if (scope.removePostTheJob) {
                scope.removePostTheJob();
            }
            scope.removePostTheJob = scope.$on('PostTheJob', function() {
                var url = (job_template.related.jobs) ? job_template.related.jobs : job_template.related.job_template + 'jobs/';
                Wait('start');
                Rest.setUrl(url);
                Rest.post(job_template).success(function (data) {
                    new_job_id = data.id;
                    launch_url = data.related.start;
                    if (data.passwords_needed_to_start.length > 0) {
                        scope.$emit('PromptForPasswords', data.passwords_needed_to_start);
                    } else {
                        scope.$emit('StartPlaybookRun', {});
                    }
                }).error(function (data, status) {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Failed to create job. POST returned status: ' + status });
                });
            });

            if (scope.removePasswordsCanceled) {
                scope.removePasswordsCanceled();
            }
            scope.removePasswordsCanceled = scope.$on('PasswordsCanceled', function() {
                // Delete the job
                Wait('start');
                Rest.setUrl(GetBasePath('jobs') + new_job_id + '/');
                Rest.destroy()
                    .success(function() {
                        Wait('stop');
                    })
                    .error(function (data, status) {
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                            msg: 'Call to ' + url + ' failed. DELETE returned status: ' + status });
                    });
            });

            if (scope.removePlaybookLaunchFinished) {
                scope.removePlaybookLaunchFinished();
            }
            scope.removePlaybookLaunchFinished = scope.$on('PlaybookLaunchFinished', function() {
                var base = $location.path().replace(/^\//, '').split('/')[0];
                if (base !== 'jobs') {
                    $location.path('/jobs');
                }
                else {
                    Wait('stop');
                }
            });

            if (scope.removeStartPlaybookRun) {
                scope.removeStartPlaybookRun();
            }
            scope.removeStartPlaybookRun = scope.$on('StartPlaybookRun', function(e, passwords) {
                LaunchJob({
                    scope: scope,
                    url: launch_url,
                    callback: 'PlaybookLaunchFinished',
                    passwords: passwords
                });
            });

            if (scope.removePromptForPasswords) {
                scope.removePromptForPasswords();
            }
            scope.removePromptForPasswords = scope.$on('PromptForPasswords', function(e, passwords) {
                PromptForPasswords({ scope: scope, passwords: passwords, callback: 'StartPlaybookRun' });
            });

            if (scope.removePromptForCredential) {
                scope.removePromptForCredential();
            }
            scope.removePromptForCredential = scope.$on('PromptForCredential', function(e, data) {
                PromptForCredential({ scope: scope, template: data });
            });

            if (scope.removeCredentialReady) {
                scope.removeCredentialReady();
            }
            scope.removeCredentialReady = scope.$on('CredentialReady', function(e, credential) {
                if (!Empty(credential)) {
                    job_template.credential = credential;
                    scope.$emit('PostTheJob');
                }
            });

            // Get the job or job_template record
            Wait('start');
            Rest.setUrl(url);
            Rest.get()
                .success(function (data) {
                    delete data.id;
                    job_template = data;
                    if (Empty(data.credential)) {
                        scope.$emit('PromptForCredential');
                    } else {
                        // We have what we need, submit the job
                        scope.$emit('PostTheJob');
                    }
                })
                .error(function (data, status) {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Failed to get job template details. GET returned status: ' + status });
                });
        };
    }
])


// Submit SCM Update request
.factory('ProjectUpdate', ['PromptForPasswords', 'LaunchJob', 'Rest', '$location', 'GetBasePath', 'ProcessErrors', 'Alert',
    'ProjectsForm', 'Wait',
    function (PromptForPasswords, LaunchJob, Rest, $location, GetBasePath, ProcessErrors, Alert, ProjectsForm, Wait) {
        return function (params) {
            var scope = params.scope,
                project_id = params.project_id,
                url = GetBasePath('projects') + project_id + '/update/',
                project;

            if (scope.removeUpdateSubmitted) {
                scope.removeUpdateSubmitted();
            }
            scope.removeUpdateSubmitted = scope.$on('UpdateSubmitted', function() {
                // Refresh the project list after update request submitted
                if (scope.refreshJobs) {
                    Wait('stop');
                    Alert('Update Started', 'The request to start the SCM update process was submitted. ' +
                    'To monitor the update status, refresh the page by clicking the <i class="fa fa-refresh"></i> button.', 'alert-info');
                    scope.refreshJobs();
                }
                //else if (scope.refresh) {
                //    scope.refresh();
                //}
            });

            if (scope.removePromptForPasswords) {
                scope.removePromptForPasswords();
            }
            scope.removePromptForPasswords = scope.$on('PromptForPasswords', function() {
                PromptForPasswords({ scope: scope, passwords: project.passwords_needed_to_update, callback: 'StartTheUpdate' });
            });

            if (scope.removeStartTheUpdate) {
                scope.removeStartTheUpdate();
            }
            scope.removeStartTheUpdate = scope.$on('StartTheUpdate', function(e, passwords) {
                LaunchJob({ scope: scope, url: url, passwords: passwords, callback: 'UpdateSubmitted' });
            });

            // Check to see if we have permission to perform the update and if any passwords are needed
            Wait('start');
            Rest.setUrl(url);
            Rest.get()
                .success(function (data) {
                    project = data;
                    if (project.can_update) {
                        if (project.passwords_needed_to_updated) {
                            Wait('stop');
                            scope.$emit('PromptForPasswords');
                        }
                        else {
                            scope.$emit('StartTheUpdate', {});
                        }
                    }
                    else {
                        Alert('Permission Denied', 'You do not have access to update this project. Please contact your system administrator.',
                            'alert-danger');
                    }
                })
                .error(function (data, status) {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Failed to lookup project ' + url + ' GET returned: ' + status });
                });
        };
    }
])


// Submit Inventory Update request
.factory('InventoryUpdate', ['PromptForPasswords', 'LaunchJob', 'Rest', '$location', 'GetBasePath', 'ProcessErrors', 'Alert', 'Wait',
    function (PromptForPasswords, LaunchJob, Rest, $location, GetBasePath, ProcessErrors, Alert, Wait) {
        return function (params) {

            var scope = params.scope,
                url = params.url,
                //group_id = params.group_id,
                //tree_id = params.tree_id,
                //base = $location.path().replace(/^\//, '').split('/')[0],
                inventory_source;

            /*if (scope.removeHostReloadComplete) {
                scope.removeHostReloadComplete();
            }
            scope.removeHostReloadComplete = scope.$on('HostReloadComplete', function () {
                //Wait('stop');
                Alert('Update Started', 'Your request to start the inventory sync process was submitted. Monitor progress ' +
                    'by clicking the <i class="fa fa-refresh fa-lg"></i> button.', 'alert-info');
                if (scope.removeHostReloadComplete) {
                    scope.removeHostReloadComplete();
                }
            });*/

            /*function getJobID(url) {
                var result='';
                url.split(/\//).every(function(path) {
                    if (/^\d+$/.test(path)) {
                        result = path;
                        return false;
                    }
                    return true;
                });
                return result;
            }*/

            if (scope.removeUpdateSubmitted) {
                scope.removeUpdateSubmitted();
            }
            scope.removeUpdateSubmitted = scope.$on('UpdateSubmitted', function () {
                // Get the current job
                /*var path = url.replace(/update\/$/,'');
                Rest.setUrl(path);
                Rest.get()
                    .success(function(data) {
                        if (data.related.current_job) {
                            scope.$emit('WatchUpdateStatus', getJobID(data.related.current_job), group_id, tree_id);
                        }
                        else {
                            Wait('stop');
                        }
                    })
                    .error(function(data, status) {
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                            msg: 'Failed to get inventory source ' + url + ' GET returned: ' + status });
                    });
                */
                //console.log('job submitted. callback returned: ');
                //console.log(data);
                /*setTimeout(function() {
                    if (base === 'jobs') {
                        scope.refreshJobs();
                    }
                    else if (scope.refreshGroups) {
                        scope.selected_tree_id = tree_id;
                        scope.selected_group_id = group_id;
                        scope.refreshGroups();
                    } else if (scope.refresh) {
                        scope.refresh();
                    }
                    scope.$emit('HostReloadComplete');
                }, 300);*/
            });

            if (scope.removePromptForPasswords) {
                scope.removePromptForPasswords();
            }
            scope.removePromptForPasswords = scope.$on('PromptForPasswords', function() {
                PromptForPasswords({ scope: scope, passwords: inventory_source.passwords_needed_to_update, callback: 'StartTheUpdate' });
            });

            if (scope.removeStartTheUpdate) {
                scope.removeStartTheUpdate();
            }
            scope.removeStartTheUpdate = scope.$on('StartTheUpdate', function(e, passwords) {
                LaunchJob({ scope: scope, url: url, passwords: passwords, callback: 'UpdateSubmitted' });
            });

            // Check to see if we have permission to perform the update and if any passwords are needed
            Wait('start');
            Rest.setUrl(url);
            Rest.get()
                .success(function (data) {
                    inventory_source = data;
                    if (data.can_update) {
                        if (data.passwords_needed_to_update) {
                            Wait('stop');
                            scope.$emit('PromptForPasswords');
                        }
                        else {
                            scope.$emit('StartTheUpdate', {});
                        }
                    } else {
                        Wait('stop');
                        Alert('Permission Denied', 'You do not have access to run the inventory sync. Please contact your system administrator.',
                            'alert-danger');
                    }
                })
                .error(function (data, status) {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Failed to get inventory source ' + url + ' GET returned: ' + status });
                });
        };
    }
]);