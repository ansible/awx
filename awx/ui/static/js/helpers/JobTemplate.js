/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  JobTemplateHelper
 * 
 */
angular.module('JobTemplateHelper', [ 'RestServices', 'Utilities', 'CredentialFormDefinition', 'CredentialsListDefinition',
    'LookUpHelper', 'JobTemplateFormDefinition' ])

    .factory('PromptPasswords',['CredentialForm', '$compile', 'Rest', '$location',
    function(JobTemplateForm, $compile, Rest, $location) {
    return function(params) {
        
        var scope = params.scope; 
        var passwords = params.passwords;
        var start_url = params.start_url;
        var form = JobTemplateForm;
        var html = '';
        var field, element, dialogScope, fld;
        
        scope.startJob = function() {
            $('#password-modal').modal('hide');
            var pswd = {};  
            $('.password-field').each(function(index) {
                pswd[$(this).attr('name')] = $(this).val();
                });
            Rest.setUrl(start_url); 
            Rest.post(pswd)
                .success( function(data, status, headers, config) {
                    var base = $location.path().replace(/^\//,'').split('/')[0];
                    if (base == 'jobs') {
                       scope.refreshJob();
                    } 
                    else {
                       $location.path('/jobs');
                    }
                    })
                .error( function(data, status, headers, config) { 
                    ProcessErrors(scope, data, status, null,
                        { hdr: 'Error!', msg: 'Failed to start job. POST returned status: ' + status });
                    });
            }
        

        html += html += "<form class=\"form-horizontal\" name=\"password_form\" novalidate>\n";    
        for (var i=0; i < passwords.length; i++) {
            // Add the password field
            field = form.fields[passwords[i]];
            fld = passwords[i];
            scope[fld] = '';
            html += "<div class=\"control-group\">\n";
            html += "<label class=\"control-label\" for=\"" + fld + '">' + field.label + '</label>' + "\n";
            html += "<div class=\"controls\">\n"; 
            html += "<input type=\"password\" ";
            html += "ng-model=\"" + fld + '" ';
            html += 'name="' + fld + '" ';
            html += "class=\"password-field\" ";
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
            field = form.fields[field.associated];
            scope[fld] = '';
            html += "<div class=\"control-group\">\n";
            html += "<label class=\"control-label\" for=\"" + fld + '">' + field.label + '</label>' + "\n";
            html += "<div class=\"controls\">\n"; 
            html += "<input type=\"password\" ";
            html += "ng-model=\"" + fld + '" ';
            html += 'name="' + fld + '" ';
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
        element = angular.element(document.getElementById('password-body'));
        element.html(html);
        $compile(element.contents())(scope);
        $('#password-modal').modal();
        }
    }])
    
    .factory('SubmitJob',['PromptPasswords', '$compile', 'Rest', '$location', 'GetBasePath', 'CredentialList',
    'LookUpInit', 'JobTemplateForm', 'ProcessErrors',
    function(PromptPasswords, $compile, Rest, $location, GetBasePath, CredentialList, LookUpInit, JobTemplateForm,
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
                    if (data.passwords_needed_to_start.length > 0) {
                       // Passwords needed. Prompt for passwords, then start job.
                       PromptPasswords({
                           scope: scope,
                           passwords: data.passwords_needed_to_start,
                           start_url: data.related.start
                           });
                    }
                    else {
                       // No passwords needed, start the job!
                       Rest.setUrl(data.related.start); 
                       Rest.post()
                           .success( function(data, status, headers, config) {
                               var base = $location.path().replace(/^\//,'').split('/')[0];
                               if (base == 'jobs') {
                                  scope.refreshJob();
                               } 
                               else {
                                  $location.path('/jobs');
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
    }]);
























