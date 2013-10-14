/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  JobSubmission.js
 * 
 */
angular.module('JobSubmissionHelper', [ 'RestServices', 'Utilities', 'CredentialFormDefinition', 'CredentialsListDefinition',
    'LookUpHelper', 'ProjectFormDefinition', 'JobSubmissionHelper', 'GroupFormDefinition', 'GroupsHelper' ])

    .factory('PromptPasswords', ['CredentialForm', 'JobTemplateForm', 'GroupForm', 'ProjectsForm', '$compile', 'Rest', '$location', 'ProcessErrors',
        'GetBasePath', 'Alert',
    function(CredentialForm, JobTemplateForm, ProjectsForm, GroupForm, $compile, Rest, $location, ProcessErrors, GetBasePath, Alert) {
    return function(params) {
        
        var scope = params.scope; 
        var passwords = params.passwords;
        var start_url = params.start_url;
        var form = params.form;
        var html = '';
        var field, element, dialogScope, fld;
        var base = $location.path().replace(/^\//,'').split('/')[0];
        var extra_html = params.extra_html;

        function navigate(canceled) {
            //Decide where to send the user once the modal dialog closes
            if (!canceled) {
               if (base == 'jobs') {
                  scope.refreshJob();
               }
               else {
                  $location.path('/jobs');
               }
            } 
            else {
               $location.path('/' + base);
            }
            }

        function cancel() {
            // Delete a job
            var url = GetBasePath('jobs') + scope.job_id +'/'
            Rest.setUrl(url);
            Rest.destroy()
                .success ( function(data, status, headers, config) {
                    if (form.name == 'credential') {
                       navigate(true);
                    }
                    })
                .error( function(data, status, headers, config) {
                    ProcessErrors(scope, data, status, null,
                        { hdr: 'Error!', msg: 'Call to ' + url + ' failed. DELETE returned status: ' + status });
                    });
            }

        scope.cancelJob = function() {
            // User clicked cancel button
            $('#password-modal').modal('hide');
            if (form.name == 'credential') {
               cancel();
            }
            else {
               scope.$emit('UpdateSubmitted','canceled');
            }
            }
        
        scope.startJob = function() {
            $('#password-modal').modal('hide');
            var pswd = {};
            var value_supplied = false;
            $('.password-field').each(function(index) {
                pswd[$(this).attr('name')] = $(this).val();
                if ($(this).val() != '' && $(this).val() !== null) {
                   value_supplied = true;
                }
                });
            if (passwords.length == 0 || value_supplied) {
               Rest.setUrl(start_url);
               Rest.post(pswd)
                   .success( function(data, status, headers, config) {
                       scope.$emit('UpdateSubmitted','started');
                       if (form.name == 'credential') {
                          navigate(false);
                       }
                       })
                   .error( function(data, status, headers, config) { 
                       ProcessErrors(scope, data, status, null,
                           { hdr: 'Error!', msg: 'POST to ' + start_url + ' failed with status: ' + status });
                       });
            }
            else {
               Alert('No Passwords', 'Required password(s) not provided. The request was not submitted.', 'alert-info');
               if (form.name == 'credential') {
                  // No passwords provided, so we can't start the job. Rather than leave the job in a 'new'
                  // state, let's delete it. 
                  cancelJob();
               }   
            }
            }
        
        if (passwords.length > 0) {
           // Prompt for passwords
           console.log(passwords);
           html += "<form class=\"form-horizontal\" name=\"password_form\" novalidate>\n";
           html += (extra_html) ? extra_html : "";
           var current_form;
           for (var i=0; i < passwords.length; i++) {
               // Add the password field
               if (form.name == 'credential') {
                  // this is a job. we could be prompting for inventory and/or SCM passwords
                  if (form.fields[passwords[i]]) {
                     current_form = form;
                  }
                  else if (ProjectsForm.fields[passwords[i]]) {
                     current_form = ProjectsForm;
                  }
                  else if (GroupForm.fields[passwords[i]]) {
                     current_form = GroupForm;
                  }
                  else {
                     // No match found. Abandon ship!
                     Alert('Form Not Found', 'Could not locate form for: ' + passwords[i], 'alert-danger');
                     $location('/#/jobs');
                  }
               }
               else {
                  current_form = form;
               }
               field = current_form.fields[passwords[i]];
               fld = passwords[i];
               scope[fld] = '';
               html += "<div class=\"form-group\">\n";
               html += "<label class=\"control-label col-lg-3 normal-weight\" for=\"" + fld + "\">* ";
               html += (field.labelBind) ? scope[field.labelBind] : field.label;
               html += "</label>\n";
               html += "<div class=\"col-lg-9\">\n"; 
               html += "<input type=\"password\" ";
               html += "ng-model=\"" + fld + '" ';
               html += 'name="' + fld + '" ';
               html += "class=\"password-field form-control\" ";
               html += "required ";
               html += "/>";
               html += "<br />\n";
               // Add error messages
               html += "<span class=\"error\" ng-show=\"password_form." + fld + ".$dirty && " + 
                   "password_form." + fld + ".$error.required\">A value is required!</span>\n";
               html += "<span class=\"error api-error\" ng-bind=\"" + fld + "_api_error\"></span>\n";
               html += "</div>\n";
               html += "</div>\n";
             
               // Add the related confirm field
               fld = field.associated;
               field = current_form.fields[field.associated];
               scope[fld] = '';
               html += "<div class=\"form-group\">\n";
               html += "<label class=\"control-label col-lg-3 normal-weight\" for=\"" + fld + "\">* ";
               html += (field.labelBind) ? scope[field.labelBind] : field.label;
               html += "</label>\n";
               html += "<div class=\"col-lg-9\">\n"; 
               html += "<input type=\"password\" ";
               html += "ng-model=\"" + fld + '" ';
               html += 'name="' + fld + '" ';
               html += "class=\"form-control\" ";
               html += "required ";
               html += (field.awPassMatch) ? "awpassmatch=\"" + field.associated + "\" " : "";
               html += "/>";
               html += "<br />\n";
               // Add error messages
               html += "<span class=\"error\" ng-show=\"password_form." + fld + ".$dirty && " + 
                   "password_form." + fld + ".$error.required\">A value is required!</span>\n";     
               if (field.awPassMatch) {
                  html += "<span class=\"error\" ng-show=\"password_form." + fld + 
                      ".$error.awpassmatch\">Must match Password value</span>\n";
               }
               html += "<span class=\"error api-error\" ng-bind=\"" + fld + "_api_error\"></span>\n";
               html += "</div>\n";
               html += "</div>\n";
            }
            html += "</form>\n";
            var element = angular.element(document.getElementById('password-body'));
            element.html(html);
            $compile(element.contents())(scope);
            $('#password-modal').modal();
            $('#password-modal').on('shown.bs.modal', function() {
                 $('#password-body').find('input[type="password"]:first').focus();
                 });
        }
        else {
            scope.startJob();
        }
        }
        }])
    
    .factory('SubmitJob',['PromptPasswords', '$compile', 'Rest', '$location', 'GetBasePath', 'CredentialList',
    'LookUpInit', 'CredentialForm', 'ProcessErrors',
    function(PromptPasswords, $compile, Rest, $location, GetBasePath, CredentialList, LookUpInit, CredentialForm,
        ProcessErrors) {
    return function(params) {
        var scope = params.scope; 
        var id = params.id;
        var template_name = (params.template) ? params.template : null;
        var base = $location.path().replace(/^\//,'').split('/')[0];
        var url = GetBasePath(base) + id + '/';

        function postJob(data) {
            // Create the job record
            if (scope.credentialWatchRemove) {
                 scope.credentialWatchRemove();
            }
            var dt = new Date().toISOString();
            var url = (data.related.jobs) ? data.related.jobs : data.related.job_template + 'jobs/';
            var name = (template_name) ? template_name : data.name;
            Rest.setUrl(url);
            Rest.post({
                name: name + ' ' + dt,        // job name required and unique
                description: data.description, 
                job_template: data.id, 
                inventory: data.inventory, 
                project: data.project, 
                playbook: data.playbook, 
                credential: data.credential, 
                forks: data.forks, 
                limit: data.limit, 
                verbosity: data.verbosity, 
                extra_vars: data.extra_vars
                })
                .success( function(data, status, headers, config) {
                    scope.job_id = data.id;
                    if (data.passwords_needed_to_start.length > 0) {
                       // Passwords needed. Prompt for passwords, then start job.
                       PromptPasswords({
                           scope: scope,
                           passwords: data.passwords_needed_to_start,
                           start_url: data.related.start,
                           form: CredentialForm
                           });
                    }
                    else {
                       // No passwords needed, start the job!
                       Rest.setUrl(data.related.start); 
                       Rest.post()
                           .success( function(data, status, headers, config) {
                               var base = $location.path().replace(/^\//,'').split('/')[0];
                               if (base == 'jobs') {
                                  scope.refresh();
                               } 
                               else {
                                  $location.url('/#/jobs');
                               }
                               })
                           .error( function(data, status, headers, config) { 
                               ProcessErrors(scope, data, status, null,
                                   { hdr: 'Error!', msg: 'Failed to start job. POST returned status: ' + status });
                               });
                    }
                    })
                .error( function(data, status, headers, config) {
                    ProcessErrors(scope, data, status, null,
                       { hdr: 'Error!', msg: 'Failed to create job. POST returned status: ' + status });
                    });
            };
        
        // Get the job or job_template record
        Rest.setUrl(url);
        Rest.get()
            .success( function(data, status, headers, config) {
                // Create a job record
                scope.credential = '';
                if (data.credential == '' || data.credential == null) {
                   // Template does not have credential, prompt for one
                   if (scope.credentialWatchRemove) {
                      scope.credentialWatchRemove();
                   }
                   scope.credentialWatchRemove = scope.$watch('credential', function(newVal, oldVal) {
                       if (newVal !== oldVal) {
                          // After user selects a credential from the modal,
                          // submit the job
                          if (scope.credential != '' && scope.credential !== null && scope.credential !== undefined) {
                             data.credential = scope.credential;
                             postJob(data);
                          }
                       }
                       });
                   LookUpInit({
                       scope: scope,
                       form: JobTemplateForm,
                       current_item: null,
                       list: CredentialList, 
                       field: 'credential',
                       hdr: 'Credential Required'
                       });
                   scope.lookUpCredential();
                }
                else {
                   // We have what we need, submit the job
                   postJob(data);
                }
            })
            .error( function(data, status, headers, config) {
                ProcessErrors(scope, data, status, null,
                    { hdr: 'Error!', msg: 'Failed to get job template details. GET returned status: ' + status });
            });
            };
    }])
    
    // Sumbit SCM Update request
    .factory('ProjectUpdate',['PromptPasswords', '$compile', 'Rest', '$location', 'GetBasePath', 'ProcessErrors', 'Alert',
        'ProjectsForm',
    function(PromptPasswords, $compile, Rest, $location, GetBasePath, ProcessErrors, Alert, ProjectsForm) { 
    return function(params) {
        var scope = params.scope; 
        var project_id = params.project_id;
        var url = GetBasePath('projects') + project_id + '/update/';
        
        if (scope.removeUpdateSubmitted) {
           scope.removeUpdateSubmitted();
        }
        scope.removeUpdateSubmitted = scope.$on('UpdateSubmitted', function(e, action) {
            // Refresh the project list after update request submitted
            Alert('Update Started', 'The request to start the SCM update process was submitted. ' +
                'The Projects page will refresh every 10 seconds, or refresh manually by clicking the <em>Refresh</em> button.', 'alert-info');
            scope.refresh();
            });
        
        if (scope.removeSCMSubmit) {
           scope.removeSCMSubmit();
        }
        scope.removeSCMSubmit = scope.$on('SCMSubmit', function(e, passwords_needed_to_update, extra_html) {
            // After the call to update, kick off the job.
            PromptPasswords({
                       scope: scope,
                       passwords: passwords_needed_to_update,
                       start_url: url, 
                       form: ProjectsForm,
                       extra_html: extra_html
                       });
            });
        
        // Check to see if we have permission to perform the update and if any passwords are needed
        Rest.setUrl(url);
        Rest.get()
            .success( function(data, status, headers, config) {
                if (data.can_update) {
                   var extra_html = '';
                   for (var i=0; i < scope.projects.length; i++) {
                       if (scope.projects[i].id == project_id) {
                          extra_html += "<div class=\"form-group\">\n";
                          extra_html += "<label class=\"control-label col-lg-3 normal-weight\" for=\"scm_url\">SCM URL</label>\n";
                          extra_html += "<div class=\"col-lg-9\">\n"; 
                          extra_html += "<input type=\"text\" readonly";
                          extra_html += ' name=\"scm_url\" ';
                          extra_html += "class=\"form-control\" ";
                          extra_html += "value=\"" + scope.projects[i].scm_url + "\" ";
                          extra_html += "/>";
                          extra_html += "</div>\n";
                          extra_html += "</div>\n";
                          if (scope.projects[i].scm_username) {
                             extra_html += "<div class=\"form-group\">\n";
                             extra_html += "<label class=\"control-label col-lg-3 normal-weight\" for=\"scm_username\">SCM Username</label>\n";
                             extra_html += "<div class=\"col-lg-9\">\n"; 
                             extra_html += "<input type=\"text\" readonly";
                             extra_html += ' name=\"scm_username\" ';
                             extra_html += "class=\"form-control\" ";
                             extra_html += "value=\"" + scope.projects[i].scm_username + "\" ";
                             extra_html += "/>";
                             extra_html += "</div>\n";
                             extra_html += "</div>\n"; 
                          }                        
                          break;
                       }
                   }
                   extra_html += "</p>";
                   scope.$emit('SCMSubmit', data.passwords_needed_to_update, extra_html);
                } 
                else {
                   Alert('Permission Denied', 'You do not have access to update this project. Please contact your system administrator.', 
                       'alert-danger');
                }   
            })
            .error( function(data, status, headers, config) {
                ProcessErrors(scope, data, status, null,
                    { hdr: 'Error!', msg: 'Failed to get project update details: ' +  url + ' GET status: ' + status });
            });
            };
    }])


    // Sumbit Inventory Update request
    .factory('InventoryUpdate',['PromptPasswords', '$compile', 'Rest', '$location', 'GetBasePath', 'ProcessErrors', 'Alert', 
        'GroupForm', 'InventorySummary',
    function(PromptPasswords, $compile, Rest, $location, GetBasePath, ProcessErrors, Alert, GroupForm, InventorySummary) { 
    return function(params) {
        
        var scope = params.scope; 
        var inventory_id = params.inventory_id;
        var url = params.url;
        var group_id = params.group_id; 
        var group_name = params.group_name;
        var group_source = params.group_source; 

        if (scope.removeUpdateSubmitted) {
           scope.removeUpdateSubmitted();
        }
        scope.removeUpdateSubmitted = scope.$on('UpdateSubmitted', function(e, action) {
            if (action == 'started') {
               // Refresh the project list after update request submitted
               Alert('Update Started', 'The request to start the inventory update process was submitted. Monitor progress from the inventory summary screen. ' +
                   'The screen will refresh every 10 seconds, or refresh manually by clicking the <em>Refresh</em> button.', 'alert-info');
               var node = $('#inventory-node')
               var selected = $('#tree-view').jstree('get_selected');
               scope['inventorySummaryGroup'] = group_name; 
               selected.each(function(idx) {
                   $('#tree-view').jstree('deselect_node', $(this));
                   });
               $('#tree-view').jstree('select_node', node);
            }
            });
        
        if (scope.removeInventorySubmit) {
           scope.removeInventorySubmit();
        }
        scope.removeInventorySubmit = scope.$on('InventorySubmit', function(e, passwords_needed_to_update, extra_html) {
            // After the call to update, kick off the job.
            PromptPasswords({
                       scope: scope,
                       passwords: passwords_needed_to_update,
                       start_url: url, 
                       form: GroupForm,
                       extra_html: extra_html
                       });
            });
        
        // Check to see if we have permission to perform the update and if any passwords are needed
        Rest.setUrl(url);
        Rest.get()
            .success( function(data, status, headers, config) {
                if (data.can_update) {
                   var extra_html = "<div class=\"inventory-passwd-msg\">Starting inventory update for <em>" + group_name + 
                       "</em>. Please provide the " + group_source + " credentials:</div>\n";
                   scope.$emit('InventorySubmit', data.passwords_needed_to_update, extra_html);
                } 
                else {
                   Alert('Permission Denied', 'You do not have access to run the update. Please contact your system administrator.', 
                       'alert-danger');
                }   
            })
            .error( function(data, status, headers, config) {
                ProcessErrors(scope, data, status, null,
                    { hdr: 'Error!', msg: 'Failed to get inventory_source details. ' + url + 'GET status: ' + status });
            });
            };
    }]);

