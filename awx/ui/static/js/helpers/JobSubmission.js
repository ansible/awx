/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  JobSubmission.js
 *
 */
   /**
 * @ngdoc function
 * @name helpers.function:JobSubmission
 * @description
*/
'use strict';

angular.module('JobSubmissionHelper', [ 'RestServices', 'Utilities', 'CredentialFormDefinition', 'CredentialsListDefinition',
    'LookUpHelper', 'JobSubmissionHelper', 'JobTemplateFormDefinition', 'ModalDialog', 'FormGenerator', 'JobVarsPromptFormDefinition'])

.factory('LaunchJob', ['Rest', 'Wait', 'ProcessErrors', 'ToJSON', 'Empty',
    function(Rest, Wait, ProcessErrors, ToJSON, Empty) {
        return function(params) {
            var scope = params.scope,
                callback = params.callback || 'JobLaunched',
                job_launch_data = {},
                url = params.url,
                fld,
                extra_vars;


            if(!Empty(scope.passwords_needed_to_start) && scope.passwords_needed_to_start .length>0){
                scope.passwords.forEach(function(password) {
                        job_launch_data[password] = scope[password];
                    });
            }
            if(scope.prompt_for_vars===true){
                extra_vars = ToJSON(scope.parseType, scope.extra_vars, false);
                $.each(extra_vars, function(key,value){
                    job_launch_data[key] = value;
                });
            }
            if(scope.survey_enabled===true){
                for (fld in scope.job_launch_form){
                    if(scope[fld]){
                        job_launch_data[fld] = scope[fld];
                    }
                }
            }
            delete(job_launch_data.extra_vars);
            if(!Empty(scope.credential)){
                job_launch_data.credential = scope.credential;
            }
            Rest.setUrl(url);
            Rest.post(job_launch_data)
                .success(function(data) {
                    Wait('stop');
                    if(!$('#password-modal').is(':hidden')){
                        $('#password-modal').dialog('close');
                    }
                    scope.$emit(callback, data);
                })
                .error(function(data, status) {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Failed updating job ' + scope.job_template_id + ' with variables. PUT returned: ' + status });
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
                postAction: selectionMade,
                input_type: 'radio'
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



.factory('CreateLaunchDialog', ['$compile', 'Rest', 'GetBasePath', 'TextareaResize', 'CreateDialog', 'GenerateForm',
    'JobVarsPromptForm', 'Wait', 'ParseTypeChange',
    function($compile, Rest, GetBasePath, TextareaResize,CreateDialog, GenerateForm,
        JobVarsPromptForm, Wait, ParseTypeChange) {
    return function(params) {
        var buttons,
            scope = params.scope,
            html = params.html,
            // job_launch_data = {},
            callback = params.callback || 'PlaybookLaunchFinished',
            // url = params.url,
            e;

        // html+='<br>job_launch_form.$valid = {{job_launch_form.$valid}}<br>';
        html+='</form>';
        $('#password-modal').empty().html(html);
        $('#password-modal').find('textarea').before(scope.helpContainer);
        e = angular.element(document.getElementById('password-modal'));
        $compile(e)(scope);

        if(scope.prompt_for_vars===true){
            ParseTypeChange({ scope: scope, field_id: 'job_extra_vars' , variable: "extra_vars"});
        }

        buttons = [{
            label: "Cancel",
            onClick: function() {
                $('#password-modal').dialog('close');
                // scope.$emit('CancelJob');
                // scope.$destroy();
            },
            icon: "fa-times",
            "class": "btn btn-default",
            "id": "password-cancel-button"
        },{
            label: "Launch",
            onClick: function() {
                scope.$emit(callback);
            },
            icon: "fa-check",
            "class": "btn btn-primary",
            "id": "password-accept-button"
        }];

        CreateDialog({
            id: 'password-modal',
            scope: scope,
            buttons: buttons,
            width: 620,
            height: 700, //(scope.passwords.length > 1) ? 700 : 500,
            minWidth: 500,
            title: 'Launch Configuration',
            callback: 'DialogReady',
            onOpen: function(){
                Wait('stop');
            }
        });

        if (scope.removeDialogReady) {
            scope.removeDialogReady();
        }
        scope.removeDialogReady = scope.$on('DialogReady', function() {
            $('#password-modal').dialog('open');
            $('#password-accept-button').attr('ng-disabled', 'job_launch_form.$invalid' );
            e = angular.element(document.getElementById('password-accept-button'));
            $compile(e)(scope);
            // if(scope.prompt_for_vars===true){
            //     setTimeout(function() {
            //         TextareaResize({
            //             scope: scope,
            //             textareaId: 'job_variables',
            //             modalId: 'password-modal',
            //             formId: 'job_launch_form',
            //             parse: true
            //         });
            //     }, 300);
            // }

        });
    };

}])




.factory('PromptForPasswords', ['$compile', 'Wait', 'Alert', 'CredentialForm',
    function($compile, Wait, Alert, CredentialForm) {
        return function(params) {
            var scope = params.scope,
                callback = params.callback || 'PasswordsAccepted',
                url = params.url,
                form = CredentialForm,
                // acceptedPasswords = {},
                fld, field,
                html=params.html || "";

            scope.passwords = params.passwords;
            // Wait('stop');


            html += "<div class=\"alert alert-info\">Launching this job requires the passwords listed below. Enter and confirm each password before continuing.</div>\n";
            // html += "<form name=\"password_form\" novalidate>\n";

            scope.passwords.forEach(function(password) {
                // Prompt for password
                field = form.fields[password];
                fld = password;
                scope[fld] = '';
                html += "<div class=\"form-group prepend-asterisk\">\n";
                html += "<label for=\"" + fld + "\">" + field.label + "</label>\n";
                html += "<input type=\"password\" ";
                html += "ng-model=\"" + fld + '" ';
                // html += "ng-keydown=\"keydown($event)\" ";
                html += 'name="' + fld + '" ';
                html += "class=\"password-field form-control input-sm\" ";
                html += (field.associated) ? "ng-change=\"clearPWConfirm('" + field.associated + "')\" " : "";
                html += "required ";
                html += " >";
                // Add error messages
                html += "<div class=\"error\" ng-show=\"job_launch_form." + fld + ".$dirty && " +
                    "job_launch_form." + fld + ".$error.required\">A value is required!</div>\n";
                html += "<div class=\"error api-error\" ng-bind=\"" + fld + "_api_error\"></div>\n";
                html += "</div>\n";

                // Add the related confirm field
                if (field.associated) {
                    fld = field.associated;
                    field = form.fields[field.associated];
                    scope[fld] = '';
                    html += "<div class=\"form-group prepend-asterisk\">\n";
                    html += "<label for=\"" + fld + "\"> " + field.label + "</label>\n";
                    html += "<input type=\"password\" ";
                    html += "ng-model=\"" + fld + '" ';
                    // html += "ng-keydown=\"keydown($event)\" ";
                    html += 'name="' + fld + '" ';
                    html += "class=\"form-control input-sm\" ";
                    html += "ng-change=\"checkStatus()\" ";
                    html += "required ";
                    html += (field.awPassMatch) ? "awpassmatch=\"" + field.associated + "\" " : "";
                    html += "/>";
                    // Add error messages
                    html += "<div class=\"error\" ng-show=\"job_launch_form." + fld + ".$dirty && " +
                        "job_launch_form." + fld + ".$error.required\">A value is required!</span>\n";
                    html += (field.awPassMatch) ? "<span class=\"error\" ng-show=\"job_launch_form." + fld +
                        ".$error.awpassmatch\">Must match Password value</div>\n" : "";
                    html += "<div class=\"error api-error\" ng-bind=\"" + fld + "_api_error\"></div>\n";
                    html += "</div>\n";
                }
            });
            // html += "</form>\n";


            // $('#password-modal').empty().html(buildHtml);
            // e = angular.element(document.getElementById('password-modal'));
            // $compile(e)(scope);
            scope.$emit(callback, html, url);
            // CreateLaunchDialog({scope: scope})
            // buttons = [{
            //     label: "Cancel",
            //     onClick: function() {
            //         scope.passwordCancel();
            //     },
            //     icon: "fa-times",
            //     "class": "btn btn-default",
            //     "id": "password-cancel-button"
            // },{
            //     label: "Continue",
            //     onClick: function() {
            //         scope.passwordAccept();
            //     },
            //     icon: "fa-check",
            //     "class": "btn btn-primary",
            //     "id": "password-accept-button"
            // }];


            // CreateDialog({
            //     id: 'password-modal',
            //     scope: scope,
            //     buttons: buttons,
            //     width: 600,
            //     height: (parent_scope.passwords.length > 1) ? 700 : 500,
            //     minWidth: 500,
            //     title: 'parent_scope.passwords Required',
            //     callback: 'DialogReady'
            // });

            // if (scope.removeDialogReady) {
            //     scope.removeDialogReady();
            // }
            // scope.removeDialogReady = scope.$on('DialogReady', function() {
            //     $('#password-modal').dialog('open');
            //     $('#password-accept-button').attr({ "disabled": "disabled" });
            // });
            // scope.keydown = function(e){
            //     if(e.keyCode===13){
            //         scope.passwordAccept();
            //     }
            // };

            // scope.passwordAccept = function() {
            //     if (!scope.password_form.$invalid) {
            //         scope.passwords.forEach(function(password) {
            //             acceptedPasswords[password] = scope[password];
            //         });
            //         $('#password-modal').dialog('close');
            //         scope.$emit(callback, acceptedPasswords);
            //     }
            // };

            // scope.passwordCancel = function() {
            //     $('#password-modal').dialog('close');
            //     scope.$emit('CancelJob');
            //     scope.$destroy();
            // };

            // Password change
            scope.clearPWConfirm = function (fld) {
                // If password value changes, make sure password_confirm must be re-entered
                scope[fld] = '';
                scope.job_launch_form[fld].$setValidity('awpassmatch', false);
                scope.checkStatus();
            };

            scope.checkStatus = function() {
                if (!scope.job_launch_form.$invalid) {
                    $('#password-accept-button').removeAttr('disabled');
                }
                else {
                    $('#password-accept-button').attr({ "disabled": "disabled" });
                }
            };
        };
    }])

.factory('PromptForVars', ['$compile', 'Rest', 'GetBasePath', 'TextareaResize', 'CreateLaunchDialog', 'GenerateForm', 'JobVarsPromptForm', 'Wait',
    'ParseVariableString', 'ToJSON', 'ProcessErrors', '$routeParams' ,
    function($compile, Rest, GetBasePath, TextareaResize,CreateLaunchDialog, GenerateForm, JobVarsPromptForm, Wait,
        ParseVariableString, ToJSON, ProcessErrors, $routeParams) {
    return function(params) {
        var
            // parent_scope = params.scope,
            scope = params.scope,
            callback = params.callback,
            // job = params.job,
            url = params.url,
            vars_url = GetBasePath('job_templates')+scope.job_template_id + '/',
            html = params.html || "";


        function buildHtml(extra_vars){

            html += GenerateForm.buildHTML(JobVarsPromptForm, { mode: 'edit', modal: true, scope: scope });
            html = html.replace("</form>", "");
            scope.helpContainer = "<div style=\"display:inline-block; font-size: 12px; margin-top: 6px;\" class=\"help-container pull-right\">\n" +
                "<a href=\"\" id=\"awp-promote\" href=\"\" aw-pop-over=\"{{ helpText }}\" aw-tool-tip=\"Click for help\" aw-pop-over-watch=\"helpText\" " +
                "aw-tip-placement=\"top\" data-placement=\"bottom\" data-container=\"body\" data-title=\"Help\" class=\"help-link\"><i class=\"fa fa-question-circle\">" +
                "</i> click for help</a></div>\n";

            scope.helpText = "<p>After defining any extra variables, click Continue to start the job. Otherwise, click cancel to abort.</p>" +
                "<p>Extra variables are passed as command line variables to the playbook run. It is equivalent to the -e or --extra-vars " +
                "command line parameter for ansible-playbook. Provide key/value pairs using either YAML or JSON.</p>" +
                "JSON:<br />\n" +
                "<blockquote>{<br />\"somevar\": \"somevalue\",<br />\"password\": \"magic\"<br /> }</blockquote>\n" +
                "YAML:<br />\n" +
                "<blockquote>---<br />somevar: somevalue<br />password: magic<br /></blockquote>\n" +
                "<div class=\"popover-footer\"><span class=\"key\">esc</span> or click to close</div>\n";

            scope.extra_vars = ParseVariableString(extra_vars);
            scope.parseType = 'yaml';
            scope.$emit(callback, html, url);
        }

        Rest.setUrl(vars_url);
        Rest.get()
            .success(function (data) {
                buildHtml(data.extra_vars);

            })
        .error(function (data, status) {
            ProcessErrors(scope, data, status, { hdr: 'Error!',
                msg: 'Failed to retrieve organization: ' + $routeParams.id + '. GET status: ' + status });
        });



    };
}])

.factory('PromptForSurvey', ['$compile', 'Wait', 'Alert', 'CredentialForm', 'CreateLaunchDialog', 'SurveyControllerInit' , 'GetBasePath', 'Rest' , 'Empty',
         'GenerateForm', 'ShowSurveyModal', 'ProcessErrors', '$routeParams' ,
    function($compile, Wait, Alert, CredentialForm, CreateLaunchDialog, SurveyControllerInit, GetBasePath, Rest, Empty,
         GenerateForm, ShowSurveyModal, ProcessErrors, $routeParams) {
        return function(params) {
            var html = params.html || "",
                id= params.id,
                url = params.url,
                callback=params.callback,
                scope = params.scope,
                i, j,
                requiredAsterisk,
                requiredClasses,
                defaultValue,
                choices,
                element,
                checked, min, max,
                survey_url = GetBasePath('job_templates') + id + '/survey_spec/' ;

            function buildHtml(question, index){
                question.index = index;

                requiredAsterisk = (question.required===true) ? "prepend-asterisk" : "";
                requiredClasses = (question.required===true) ? "ng-pristine ng-invalid-required ng-invalid" : "";

                html+='<div id="taker_'+question.index+'" class="form-group '+requiredAsterisk+' ">';
                html += '<label for="'+question.variable+'">'+question.question_name+'</label>\n';

                if(!Empty(question.question_description)){
                    html += '<div class="survey_taker_description"><i>'+question.question_description+'</i></div>\n';
                }
                scope[question.variable] = question.default;

                if(question.type === 'text' ){
                    html+='<input type="text" id="'+question.variable+'" ng-model="'+question.variable+'" '+
                        'name="'+question.variable+'" '+
                        'class="form-control" ng-required='+question.required+'>'+
                        '<div class="error survey_error" ng-show="job_launch_form.'+ question.variable + '.$dirty && ' +
                        'job_launch_form.'+question.variable+'.$error.required\">A value is required!</div>'+
                        '<div class=\"error api-error\" ng-bind=\"" + fld + "_api_error\"></div>';
                }

                if(question.type === "textarea"){
                    scope[question.variable] = question.default || question.default_textarea;
                    html+='<textarea id="'+question.variable+'" name="'+question.variable+'" ng-model="'+question.variable+'" '+
                        'class="form-control final"  ng-required="'+question.required+'" rows="3"></textarea>'+
                        '<div class="error survey_error" ng-show="job_launch_form.'+ question.variable + '.$dirty && ' +
                        'job_launch_form.'+question.variable+'.$error.required\">A value is required!</div>'+
                        '<div class=\"error api-error\" ng-bind=\"" + fld + "_api_error\"></div>';
                }

                if(question.type === 'multiplechoice'){
                    choices = question.choices.split(/\n/);
                    element = (question.type==="multiselect") ? "checkbox" : 'radio';
                    question.default = (question.default) ? question.default : (question.default_multiselect) ? question.default_multiselect : "" ;
                    html+='<div class="survey_taker_input" > ';
                    for( j = 0; j<choices.length; j++){
                        checked = (!Empty(question.default) && question.default.indexOf(choices[j])!==-1) ? "checked" : "";
                        html+= '<input  type="'+element+'" class="mc" ng-model="'+question.variable+'" ng-required="'+question.required+'" name="'+question.variable+ ' " id="'+question.variable+'" value=" '+choices[j]+' " '+checked+' >' +
                        '<span>'+choices[j] +'</span><br>' ;
                    }
                    html+=  '<div class="error survey_error" ng-show="job_launch_form.'+ question.variable + '.$dirty && ' +
                        'job_launch_form.'+question.variable+'.$error.required\">A value is required!</div>'+
                        '<div class=\"error api-error\" ng-bind=\"" + fld + "_api_error\"></div>';
                    html+= '</div>'; //end survey_taker_input
                }

                if(question.type === "multiselect"){
                    //seperate the choices out into an array
                    choices = question.choices.split(/\n/);
                    question.default = (question.default) ? question.default : (question.default_multiselect) ? question.default_multiselect : "" ;
                    //ensure that the default answers are in an array
                    scope[question.variable] = question.default.split(/\n/);
                    //create a new object to be used by the surveyCheckboxes directive
                    scope[question.variable + '_object'] = {
                        name: question.variable,
                        value: (question.default.split(/\n/)[0]==="") ? [] : question.default.split(/\n/) ,
                        required: question.required,
                        options:[]
                    };
                    //load the options into the 'options' key of the new object
                    for(j=0; j<choices.length; j++){
                        scope[question.variable+'_object'].options.push( {value:choices[j]} );
                    }
                    //surveyCheckboxes takes a list of checkboxes and connects them to one scope variable
                    html += '<survey-checkboxes name="'+question.variable+'" ng-model=" '+question.variable + '_object " ng-required="'+question.required+'">'+
                        '</survey-checkboxes>{{job_launch_form.'+question.variable+'_object.$error.checkbox}}'+
                        '<div class="error survey_error" ng-show="job_launch_form.'+question.variable+'.$error.checkbox">A value is required!</div>';
                }

                if(question.type === 'integer'){
                    min = (!Empty(question.min)) ? Number(question.min) : "";
                    max = (!Empty(question.max)) ? Number(question.max) : "" ;
                    html+='<input type="number" id="'+question.variable+'" ng-model="'+question.variable+'" class="form-control" name="'+question.variable+'" ng-min="'+min+'" ng-max="'+max+'" integer>'+
                         '<div class="error survey_error" ng-show="job_launch_form.'+ question.variable + '.$dirty && ' +
                        'job_launch_form.'+question.variable+'.$error.required\">A value is required!</div>'+
                        '<div class=\"error api-error\" ng-bind=\"" + fld + "_api_error\"></div>'+
                        '<div class="error survey_error" ng-show="job_launch_form.'+question.variable+'.$error.number || job_launch_form.'+question.variable+'.$error.integer">This is not valid integer!</div>'+
                        '<div class="error survey_error" ng-show="job_launch_form.'+question.variable+'.$error.ngMin || job_launch_form.'+question.variable+'.$error.ngMax"> The value must be in range {{'+min+'}} to {{'+max+'}}!</div>';

                }

                if(question.type === "float"){
                    min = (!Empty(question.min)) ? question.min : "";
                    max = (!Empty(question.max)) ? question.max : "" ;
                    defaultValue = (!Empty(question.default)) ? question.default : (!Empty(question.default_float)) ? question.default_float : "" ;
                    html+='<input type="number" id="'+question.variable+'" ng-model="'+question.variable+'"  class=" form-control" name="'+question.variable+'" ng-min="'+min+'" ng-max="'+max+'" smart-float>'+
                        '<div class="error survey_error" ng-show="job_launch_form.'+question.variable+'.$error.number || job_launch_form.'+question.variable+'.$error.float">This is not valid float!</div>'+
                        '<div class="error survey_error" ng-show="job_launch_form.'+question.variable+'.$error.ngMin || job_launch_form.'+question.variable+'.$error.ngMax"> The value must be in range {{'+min+'}} to {{'+max+'}}!</div>';
                        // '<div class="error survey_error" ng-show="job_launch_form.'+question.variable+'.$dirty || job_launch_form.'+question.variable+'.$error.required"> A value is required!</div>';
                }
                html+='</div>';
                if(question.index === scope.survey_questions.length-1){
                    scope.$emit(callback, html, url);
                }
            }




            Rest.setUrl(survey_url);
            Rest.get()
                .success(function (data) {
                    if(!Empty(data)){
                        scope.survey_name = data.name;
                        scope.survey_description = data.description;
                        scope.survey_questions = data.spec;

                        for(i=0; i<scope.survey_questions.length; i++){
                            buildHtml(scope.survey_questions[i], i);
                        }
                    }
                })
            .error(function (data, status) {
                ProcessErrors(scope, data, status, { hdr: 'Error!',
                    msg: 'Failed to retrieve organization: ' + $routeParams.id + '. GET status: ' + status });
            });

        };
    }])





/**
* @ngdoc method
* @name helpers.function:JobSubmission#PlaybookRun
* @methodOf helpers.function:JobSubmission
* @description The playbook Run function is run when the user clicks the launch button
*
*/
// Submit request to run a playbook
.factory('PlaybookRun', ['$location','$routeParams', 'LaunchJob', 'PromptForPasswords', 'Rest', 'GetBasePath', 'Alert', 'ProcessErrors', 'Wait', 'Empty',
        'PromptForCredential', 'PromptForVars', 'PromptForSurvey' , 'CreateLaunchDialog',
    function ($location, $routeParams, LaunchJob, PromptForPasswords, Rest, GetBasePath, Alert, ProcessErrors, Wait, Empty,
        PromptForCredential, PromptForVars, PromptForSurvey, CreateLaunchDialog) {
        return function (params) {
            var //parent_scope = params.scope,
                scope = params.scope.$new(),
                id = params.id,
                system_job = params.system_job || false,
                base = $location.path().replace(/^\//, '').split('/')[0],
                url,
                extra_vars,
                new_job_id,
                launch_url,
                html;
            scope.job_template_id = id;
            if (base === 'job_templates' || base === 'portal') {
                url = GetBasePath('job_templates') + id + '/launch/';
            }
            else {
                url = GetBasePath('jobs') + id + '/relaunch/';
            }

            if(!Empty(system_job) &&  system_job === 'launch'){
                url = GetBasePath('system_job_templates') + id + '/launch/';
            }

            if (scope.removeCancelJob) {
                scope.removeCancelJob();
            }
            scope.removeCancelJob = scope.$on('CancelJob', function() {
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
            scope.removePlaybookLaunchFinished = scope.$on('PlaybookLaunchFinished', function(e, data) {
                var job = data.job || data.system_job;
                if((scope.portalMode===false || scope.$parent.portalMode===false ) && Empty(data.system_job)){
                    $location.path('/jobs/' + job);
                }

            });

            if (scope.removeStartPlaybookRun) {
                scope.removeStartPlaybookRun();
            }
            scope.removeStartPlaybookRun = scope.$on('StartPlaybookRun', function() {
                LaunchJob({
                    scope: scope,
                    url: url,
                    callback: 'PlaybookLaunchFinished'
                });

            });

            if (scope.removePromptForPasswords) {
                scope.removePromptForPasswords();
            }
            scope.removePromptForPasswords = scope.$on('PromptForPasswords', function(e, passwords_needed_to_start,html, url) {
                PromptForPasswords({ scope: scope,
                    passwords: passwords_needed_to_start,
                    callback: 'PromptForVars',
                    html: html,
                    url: url
                });
            });

            if (scope.removePromptForCredential) {
                scope.removePromptForCredential();
            }
            scope.removePromptForCredential = scope.$on('PromptForCredential', function(e, data) {
                PromptForCredential({ scope: scope, template: data });
            });

            if (scope.removePromptForVars) {
                scope.removePromptForVars();
            }
            scope.removePromptForVars = scope.$on('PromptForVars', function(e, html, url) {
                // passwords = pwds;

                if (scope.prompt_for_vars) {
                    // call prompt with callback of StartPlaybookRun, passwords
                    PromptForVars({
                        scope: scope,
                        job: {id:scope.job_template_id},
                        variables: extra_vars,
                        callback: 'PromptForSurvey',
                        html: html,
                        url: url
                    });
                }
                else {
                    scope.$emit('PromptForSurvey', html, url);
                }
            });


            if (scope.removePromptForSurvey) {
                scope.removePromptForSurvey();
            }
            scope.removePromptForSurvey = scope.$on('PromptForSurvey', function(e, html, url) {

                if (scope.survey_enabled) {
                    // call prompt with callback of StartPlaybookRun, passwords
                    PromptForSurvey({
                        scope: scope,
                        id: scope.job_template_id,
                        variables: extra_vars,
                        callback: 'CreateModal',
                        url: url,
                        html: html
                    });
                }
                else {
                    scope.$emit('CreateModal', html, url);
                    // CreateLaunchDialog({scope: scope, html: html, url: url});
                }

            });

            if (scope.removeCreateModal) {
                scope.removeCreateModal();
            }
            scope.removeCreateModal = scope.$on('CreateModal', function(e, html, url) {
                CreateLaunchDialog({
                    scope: scope,
                    html: html,
                    url: url,
                    callback: 'StartPlaybookRun'
                });
            });


            if (scope.removeCredentialReady) {
                scope.removeCredentialReady();
            }
            scope.removeCredentialReady = scope.$on('CredentialReady', function(e, credential) {
                var passwords = [];
                if (!Empty(credential)) {
                    Rest.setUrl(GetBasePath('credentials')+credential);
                    Rest.get()
                        .success(function (data) {
                            if(data.ssh_key_unlock === "ASK"){
                                passwords.push("ssh_password");
                            }
                            if(data.sudo_password === "ASK"){
                                passwords.push("sudo_password");
                            }
                            if(data.su_password === "ASK"){
                                passwords.push("su_password");
                            }
                            if(data.vault_password === "ASK"){
                                passwords.push("vault_password");
                            }
                            if(passwords.length>0){
                                scope.$emit('PromptForPasswords', passwords, html, url);
                            }
                            else if (scope.ask_variables_on_launch){
                                scope.$emit('PromptForVars', html, url);
                            }
                            else if (!Empty(scope.survey_enabled) &&  scope.survey_enabled===true) {
                                scope.$emit('PromptForSurvey', html, url);
                            }
                            else scope.$emit('StartPlaybookRun', url);
                        })
                        .error(function (data, status) {
                            ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                                msg: 'Failed to get job template details. GET returned status: ' + status });
                        });
                }

            });

            // Get the job or job_template record
            Wait('start');
            Rest.setUrl(url);
            Rest.get()
                .success(function (data) {
                    new_job_id = data.id;
                    launch_url = url;//data.related.start;
                    scope.passwords_needed_to_start = data.passwords_needed_to_start;
                    scope.prompt_for_vars = data.ask_variables_on_launch;
                    scope.survey_enabled = data.survey_enabled;
                    scope.ask_variables_on_launch = data.ask_variables_on_launch;

                    html = '<form class="ng-valid ng-valid-required" name="job_launch_form" id="job_launch_form" autocomplete="off" nonvalidate>';

                    if(data.credential_needed_to_start === true){
                        scope.$emit('PromptForCredential');
                    }
                    else if (!Empty(data.passwords_needed_to_start) && data.passwords_needed_to_start.length > 0) {
                        scope.$emit('PromptForPasswords', data.passwords_needed_to_start, html, url);
                    }
                    else if (data.ask_variables_on_launch) {
                        scope.$emit('PromptForVars', html, url);
                    }
                    else if (!Empty(data.survey_enabled) &&  data.survey_enabled===true) {
                        scope.$emit('PromptForSurvey', html, url);
                    }
                    else {
                        scope.$emit('StartPlaybookRun', url);
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
                Wait('stop');
                if (/\d$/.test($location.path())) {
                    //Request submitted from projects/N page. Navigate back to the list so user can see status
                    $location.path('/projects');
                }
                if (scope.socketStatus === 'error') {
                    Alert('Update Started', 'The request to start the SCM update process was submitted. ' +
                        'To monitor the update status, refresh the page by clicking the <i class="fa fa-refresh"></i> button.', 'alert-info');
                    if (scope.refresh) {
                        scope.refresh();
                    }
                }
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
                inventory_source;

            if (scope.removeUpdateSubmitted) {
                scope.removeUpdateSubmitted();
            }
            scope.removeUpdateSubmitted = scope.$on('UpdateSubmitted', function () {
                Wait('stop');
                if (scope.socketStatus === 'error') {
                    Alert('Sync Started', 'The request to start the inventory sync process was submitted. ' +
                        'To monitor the status refresh the page by clicking the <i class="fa fa-refresh"></i> button.', 'alert-info');
                    if (scope.refreshGroups) {
                        // inventory detail page
                        scope.refreshGroups();
                    }
                    else if (scope.refresh) {
                        scope.refresh();
                    }
                }
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