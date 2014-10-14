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

.factory('LaunchJob', ['Rest', 'Wait', 'ProcessErrors',
    function(Rest, Wait, ProcessErrors) {
        return function(params) {
            var scope = params.scope,
                passwords = params.passwords || {},
                callback = params.callback || 'JobLaunched',
                url = params.url;

            Wait('start');
            Rest.setUrl(url);
            Rest.post(passwords)
                .success(function(data) {
                    scope.new_job_id = data.job;
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



.factory('CreateLaunchDialog', ['$compile', 'Rest', 'GetBasePath', 'TextareaResize', 'CreateDialog', 'GenerateForm',
    'JobVarsPromptForm', 'Wait', 'ProcessErrors', 'ToJSON',
    function($compile, Rest, GetBasePath, TextareaResize,CreateDialog, GenerateForm,
        JobVarsPromptForm, Wait, ProcessErrors, ToJSON) {
    return function(params) {
        var buttons,
            scope = params.scope,
            html = params.html,
            job_launch_data = {},
            callback = params.callback || 'PlaybookLaunchFinished',
            url = params.url,
            e;

        html+='<br>job_launch_form.$valid = {{job_launch_form.$valid}}<br></form>';
        $('#password-modal').empty().html(html);
        $('#password-modal').find('textarea').before(scope.helpContainer);
        e = angular.element(document.getElementById('password-modal'));
        $compile(e)(scope);

        scope.jobLaunchFormAccept = function(){
            if(scope.passwords_needed_to_start.length>0){
                scope.passwords.forEach(function(password) {
                        job_launch_data[password] = scope[password];
                    });
            }
            if(scope.prompt_for_vars===true){
                job_launch_data.extra_vars = ToJSON(scope.parseType, scope.variables, true);
            }
            if(scope.survey_enabled===true){
                for ( var fld in scope.job_launch_form){
                    if(scope[fld]){
                        job_launch_data[fld] = scope[fld];
                    }
                }
            }

            Rest.setUrl(url);
            Rest.post(job_launch_data)
                .success(function(data) {
                    Wait('stop');
                    $('#password-modal').dialog('close');
                    scope.$emit(callback, data);
                    scope.$destroy();
                })
                .error(function(data, status) {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Failed updating job ' + scope.job_template_id + ' with variables. PUT returned: ' + status });
                });

        };





        buttons = [{
            label: "Cancel",
            onClick: function() {
                $('password-modal').close();
            },
            icon: "fa-times",
            "class": "btn btn-default",
            "id": "password-cancel-button"
        },{
            label: "Continue",
            onClick: function() {
                scope.jobLaunchFormAccept();
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
                acceptedPasswords = {},
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
                html += "ng-keydown=\"keydown($event)\" ";
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
                    html += "ng-keydown=\"keydown($event)\" ";
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
            scope.keydown = function(e){
                if(e.keyCode===13){
                    scope.passwordAccept();
                }
            };

            scope.passwordAccept = function() {
                if (!scope.password_form.$invalid) {
                    scope.passwords.forEach(function(password) {
                        acceptedPasswords[password] = scope[password];
                    });
                    $('#password-modal').dialog('close');
                    scope.$emit(callback, acceptedPasswords);
                }
            };

            scope.passwordCancel = function() {
                $('#password-modal').dialog('close');
                scope.$emit('CancelJob');
                scope.$destroy();
            };

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
            job = params.job,
            url = params.url,
            vars_url = GetBasePath('job_templates')+scope.job_template_id + '/',
            // e, helpContainer,
            html = params.html || "";


        function buildHtml(extra_vars){
            //  html += GenerateForm.buildHTML(JobVarsPromptForm, { mode: 'edit',  scope: scope });
            // scope.helpContainer = "<div style=\"display:inline-block; font-size: 12px; margin-top: 6px;\" class=\"help-container pull-right\">\n" +
            //     "<a href=\"\" id=\"awp-promote\" href=\"\" aw-pop-over=\"{{ helpText }}\" aw-tool-tip=\"Click for help\" aw-pop-over-watch=\"helpText\" " +
            //     "aw-tip-placement=\"top\" data-placement=\"bottom\" data-container=\"body\" data-title=\"Help\" class=\"help-link\"><i class=\"fa fa-question-circle\">" +
            //     "</i> click for help</a></div>\n";

            // scope.helpText = "<p>After defining any extra variables, click Continue to start the job. Otherwise, click cancel to abort.</p>" +
            //             "<p>Extra variables are passed as command line variables to the playbook run. It is equivalent to the -e or --extra-vars " +
            //             "command line parameter for ansible-playbook. Provide key/value pairs using either YAML or JSON.</p>" +
            //             "JSON:<br />\n" +
            //             "<blockquote>{<br />\"somevar\": \"somevalue\",<br />\"password\": \"magic\"<br /> }</blockquote>\n" +
            //             "YAML:<br />\n" +
            //             "<blockquote>---<br />somevar: somevalue<br />password: magic<br /></blockquote>\n" +
            //             "<div class=\"popover-footer\"><span class=\"key\">esc</span> or click to close</div>\n";

            // <div class="form-group">
            html+= '<div>'+
            '<div class="parse-selection" id="job_variables_parse_type">Parse as: <input type="radio" ng-disabled="disableParseSelection" ng-model="parseType" value="yaml" ng-change="parseTypeChange()" class="ng-pristine ng-valid" name="00L"> <span class="parse-label">YAML</span>'+
            '<input type="radio" ng-disabled="disableParseSelection" ng-model="parseType" value="json" ng-change="parseTypeChange()" class="ng-pristine ng-valid" name="00M"> <span class="parse-label">JSON</span>'+
            '</div>'+
            '<div style="display:inline-block; font-size: 12px; margin-top: 6px;" class="help-container pull-right">'+
            '<a href="" id="awp-promote" aw-pop-over="<p>After defining any extra variables, click Continue to start the job. Otherwise, click cancel to abort.</p><p>Extra variables are passed as command line variables to the playbook run. It is equivalent to the -e or --extra-vars command line parameter for ansible-playbook. Provide key/value pairs using either YAML or JSON.</p>JSON:<br />'+
            '<blockquote>{<br />&quot;somevar&quot;: &quot;somevalue&quot;,<br />&quot;password&quot;: &quot;magic&quot;<br /> }</blockquote>'+
            'YAML:<br />'+
            '<blockquote>---<br />somevar: somevalue<br />password: magic<br /></blockquote>'+
            '<div class=&quot;popover-footer&quot;><span class=&quot;key&quot;>esc</span> or click to close</div>'+
            '" aw-tool-tip="Click for help" aw-pop-over-watch="helpText" aw-tip-placement="top" data-placement="bottom" data-container="body" data-title="Help" class="help-link" data-original-title="" title="" tabindex="-1"><i class="fa fa-question-circle"></i> click for help</a></div>'+
            '<textarea rows="6" ng-model="variables" name="variables" class="form-control ng-pristine ng-valid" id="job_variables" aw-watch=""></textarea>'+
            '<div class="error api-error ng-binding" id="job-variables-api-error" ng-bind="variables_api_error"></div>'+
            '</div>';
            // </div>

            scope.variables = ParseVariableString(extra_vars);
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


        // CreateLaunchDialog({scope: scope, html: html})
        // Reuse password modal
        // $('#password-modal').empty().html(html);
        // $('#password-modal').find('textarea').before(helpContainer);
        // e = angular.element(document.getElementById('password-modal'));
        // $compile(e)(scope);

        // buttons = [{
        //     label: "Cancel",
        //     onClick: function() {
        //         scope.varsCancel();
        //     },
        //     icon: "fa-times",
        //     "class": "btn btn-default",
        //     "id": "vars-cancel-button"
        // },{
        //     label: "Continue",
        //     onClick: function() {
        //         scope.varsAccept();
        //     },
        //     icon: "fa-check",
        //     "class": "btn btn-primary",
        //     "id": "vars-accept-button"
        // }];

        // if (scope.removeDialogReady) {
        //     scope.removeDialogReady();
        // }
        // scope.removeDialogReady = scope.$on('DialogReady', function() {
        //     Wait('stop');
        //     $('#password-modal').dialog('open');
        //     setTimeout(function() {
        //         TextareaResize({
        //             scope: scope,
        //             textareaId: 'job_variables',
        //             modalId: 'password-modal',
        //             formId: 'job_form',
        //             parse: true
        //         });
        //     }, 300);
        // });

        // CreateDialog({
        //     id: 'password-modal',
        //     scope: scope,
        //     buttons: buttons,
        //     width: 575,
        //     height: 530,
        //     minWidth: 450,
        //     title: 'Extra Variables',
        //     onResizeStop: function() {
        //         TextareaResize({
        //             scope: scope,
        //             textareaId: 'job_variables',
        //             modalId: 'password-modal',
        //             formId: 'job_form',
        //             parse: true
        //         });
        //     },
        //     beforeDestroy: function() {
        //         if (scope.codeMirror) {
        //             scope.codeMirror.destroy();
        //         }
        //         $('#password-modal').empty();
        //     },
        //     onOpen: function() {
        //         $('#job_variables').focus();
        //     },
        //     callback: 'DialogReady'
        // });

        scope.varsCancel = function() {
            $('#password-modal').dialog('close');
            scope.$emit('CancelJob');
            scope.$destroy();
        };

        scope.varsAccept = function() {
            job.extra_vars = ToJSON(scope.parseType, scope.variables, true);
            Wait('start');
            //Rest.setUrl(GetBasePath('jobs') + job.id + '/');
            Rest.setUrl(url);
            Rest.put(job)
                .success(function() {
                    Wait('stop');
                    $('#password-modal').dialog('close');
                    scope.$emit(callback);
                    scope.$destroy();
                })
                .error(function(data, status) {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Failed updating job ' + job.id + ' with variables. PUT returned: ' + status });
                });
        };

    };
}])

.factory('PromptForSurvey', ['$compile', 'Wait', 'Alert', 'CredentialForm', 'CreateLaunchDialog', 'SurveyControllerInit' , 'GetBasePath', 'Rest' , 'Empty',
        'SurveyTakerForm', 'GenerateForm', 'ShowSurveyModal', 'ProcessErrors', '$routeParams' ,
    function($compile, Wait, Alert, CredentialForm, CreateLaunchDialog, SurveyControllerInit, GetBasePath, Rest, Empty,
        SurveyTakerForm, GenerateForm, ShowSurveyModal, ProcessErrors, $routeParams) {
        return function(params) {
            var html = params.html || "",
                form = SurveyTakerForm,
                id= params.id,
                url = params.url,
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

                if(!$('#taker_'+question.index+':eq(0)').is('div')){
                    html+='<div id="taker_'+question.index+'" class="survey_taker_question row">';
                    $('#survey_taker_finalized_questions').append(html);
                }

                requiredAsterisk = (question.required===true) ? "prepend-asterisk" : "";
                requiredClasses = (question.required===true) ? "ng-pristine ng-invalid-required ng-invalid" : "";
                html += '<div class="col-xs-12 '+requiredAsterisk+'"><b>'+question.question_name+'</b></div>\n';
                if(!Empty(question.question_description)){
                    html += '<div class="col-xs-12 survey_taker_description"><i>'+question.question_description+'</i></div>\n';
                }
                scope[question.variable] = question.default;
                if(question.type === 'text' ){
                    //defaultValue = (question.default) ? question.default : "";

                    html+='<div class="row">'+
                        '<div class="col-xs-8">'+
                        '<input type="text" id="'+question.variable+'" ng-model="'+question.variable+'" '+
                        'name="'+question.variable+'" '+
                        'class="form-control survey_taker_input ng-pristine ng-invalid-required ng-invalid" required="" >'+
                        '<div class="error survey_error" ng-show="job_launch_form.'+ question.variable + '.$dirty && ' +
                        'job_launch_form.'+question.variable+'.$error.required\">A value is required!</div>'+
                        '<div class=\"error api-error\" ng-bind=\"" + fld + "_api_error\"></div>'+
                        '</div>'+
                        '</div>';

                }
                if(question.type === "textarea"){
                    scope[question.variable] = question.default || question.default_textarea;
                    html+='<div class="row">'+
                        '<div class="col-xs-8">'+
                        '<textarea id="'+question.variable+'" name="'+question.variable+'" ng-model="'+question.variable+'" '+
                        'class="form-control survey_taker_input ng-pristine ng-invalid-required ng-invalid final"  required="" rows="3"></textarea>'+
                        '<div class="error survey_error" ng-show="job_launch_form.'+ question.variable + '.$dirty && ' +
                        'job_launch_form.'+question.variable+'.$error.required\">A value is required!</div>'+
                        '<div class=\"error api-error\" ng-bind=\"" + fld + "_api_error\"></div>'+
                        '</div></div>';
                }
                if(question.type === 'multiplechoice'){
                    choices = question.choices.split(/\n/);
                    element = (question.type==="multiselect") ? "checkbox" : 'radio';
                    question.default = (question.default) ? question.default : (question.default_multiselect) ? question.default_multiselect : "" ;

                    html+='<div class="survey_taker_input" > ';

                    for( j = 0; j<choices.length; j++){
                        checked = (!Empty(question.default) && question.default.indexOf(choices[j])!==-1) ? "checked" : "";
                        // html+='<label class="'+element+'-inline">'+
                        // '<input class="survey_taker_input" type="'+element+'" name="'+question.variable+ ' " id="" value=" '+choices[j]+' " '+checked+' >' +choices[j]+
                        // '</label>';
                        html+= '<input  type="'+element+'" ng-model="'+question.variable+'" ng-required="!'+question.variable+'" name="'+question.variable+ ' " id="'+question.variable+'" value=" '+choices[j]+' " '+checked+' >' +
                        '<span>'+choices[j] +'</span><br>' ;

                    }
                    html+=  '<div class="error survey_error" ng-show="job_launch_form.'+ question.variable + '.$dirty && ' +
                        'job_launch_form.'+question.variable+'.$error.required\">A value is required!</div>'+
                        '<div class=\"error api-error\" ng-bind=\"" + fld + "_api_error\"></div>';
                    html+= '</div>';
                }
                if(question.type === "multiselect"){
                    choices = question.choices.split(/\n/);
                    element = (question.type==="multiselect") ? "checkbox" : 'radio';
                    question.default = (question.default) ? question.default : (question.default_multiselect) ? question.default_multiselect : "" ;
                    // scope[question.variable].choices = choices;
                    html+='<div class="survey_taker_input" > ';

                    for( j = 0; j<choices.length; j++){
                        checked = (!Empty(question.default) && question.default.indexOf(choices[j])!==-1) ? "checked" : "";
                        html+= '<input  type="checkbox"  ng-required="!'+question.variable+'" name="'+question.variable+ ' " id="'+question.variable+'" value=" '+choices[j]+' " '+checked+' >' +
                        '<span>'+choices[j] +'</span><br>' ;

                    }
                    html+=  '<div class="error survey_error" ng-show="job_launch_form.'+ question.variable + '.$dirty && ' +
                        'job_launch_form.'+question.variable+'.$error.required\">A value is required!</div>'+
                        '<div class=\"error api-error\" ng-bind=\"" + fld + "_api_error\"></div>';
                    html+= '</div>';
                }
                if(question.type === 'integer'){
                    min = (!Empty(question.min)) ? Number(question.min) : "";
                    max = (!Empty(question.max)) ? Number(question.max) : "" ;
                    //defaultValue = (!Empty(question.default)) ? question.default : (!Empty(question.default_int)) ? question.default_int : "" ;
                    html+='<div class="row">'+
                        '<div class="col-xs-8">'+
                        '<input type="number" id="'+question.variable+'" class="survey_taker_input form-control" name="'+question.variable+'" ng-min="'+min+'" ng-max="'+max+'" ng-model="'+question.variable+' " integer>'+
                        '<div class="error survey_error" ng-show="job_launch_form.'+question.variable+'.$error.number || job_launch_form.'+question.variable+'.$error.integer">This is not valid integer!</div>'+
                        '<div class="error survey_error" ng-show="job_launch_form.'+question.variable+'.$error.ngMin || job_launch_form.'+question.variable+'.$error.ngMax"> The value must be in range {{'+min+'}} to {{'+max+'}}!</div>'+
                        '</div></div>';

                }
                if(question.type === "float"){
                    min = (!Empty(question.min)) ? question.min : "";
                    max = (!Empty(question.max)) ? question.max : "" ;
                    defaultValue = (!Empty(question.default)) ? question.default : (!Empty(question.default_float)) ? question.default_float : "" ;
                    html+='<div class="row">'+
                        '<div class="col-xs-8">'+
                        '<input type="number" id="'+question.variable+'" class="survey_taker_input form-control" name="'+question.variable+'" ng-min="'+min+'" ng-max="'+max+'" ng-model="'+question.variable+'" smart-float>'+
                        '<div class="error survey_error" ng-show="job_launch_form.'+question.variable+'.$error.number || job_launch_form.'+question.variable+'.$error.float">This is not valid float!</div>'+
                        '<div class="error survey_error" ng-show="job_launch_form.'+question.variable+'.$error.ngMin || job_launch_form.'+question.variable+'.$error.ngMax"> The value must be in range {{'+min+'}} to {{'+max+'}}!</div>'+
                        '</div></div>';

                }
                html+='</div>';
                if(question.index === scope.survey_questions.length-1){
                    CreateLaunchDialog({scope: scope, html: html, url: url});
                }
            }

            scope.someSelected = function (object) {
                return Object.keys(object).some(function (key) {
                    return object[key];
                });
            };

                // question.index = index;
                // question[question.variable] = question.default;
                // scope[question.variable] = question.default;


                // if(!$('#question_'+question.index+':eq(0)').is('div')){
                //     html+='<div id="question_'+question.index+'" class="survey_taker_question_final row"></div>';
                //     $('#survey_taker_finalized_questions').append(html);
                // }

                // requiredAsterisk = (question.required===true) ? "prepend-asterisk" : "";
                // requiredClasses = (question.required===true) ? "ng-pristine ng-invalid-required ng-invalid" : "";

                // html += '<div class="col-xs-12 '+requiredAsterisk+'"><b>'+question.question_name+'</b></div>\n';
                // if(!Empty(question.question_description)){
                //     html += '<div class="col-xs-12 description"><i>'+question.question_description+'</i></div>\n';
                // }
                // defaultValue = (question.default) ? question.default : "";

                // if(question.type === 'text' ){
                //     html+='<div class="row">'+
                //         '<div class="col-xs-8">'+
                //         '<input type="text" ng-model="'+question.variable+'" '+         //placeholder="'+defaultValue+'"
                //                 'class="form-control '+requiredClasses+' final" required="" >'+
                //         '</div></div>';
                // }
                // if(question.type === "textarea"){
                //     html+='<div class="row">'+
                //         '<div class="col-xs-8">'+
                //         '<textarea ng-model="'+question.variable+'" class="form-control '+requiredClasses+' final" required="" rows="3" >'+//defaultValue+
                //                 '</textarea>'+
                //         '</div></div>';
                // }
                // if(question.type === 'multiplechoice' || question.type === "multiselect"){
                //     choices = question.choices.split(/\n/);
                //     element = (question.type==="multiselect") ? "checkbox" : 'radio';

                //     for( i = 0; i<choices.length; i++){
                //         checked = (!Empty(question.default) && question.default.indexOf(choices[i].trim())!==-1) ? "checked" : "";
                //         html+='<label class="'+element+'-inline  final">'+
                //         '<input type="'+element+'" name="'+question.variable+ ' " id="" value=" '+choices[i]+' " '+checked+' >' +choices[i]+
                //         '</label>';
                //     }

                // }
                // if(question.type === 'integer' || question.type === "float"){
                //     min = (question.min) ? question.min : "";
                //     max = (question.max) ? question.max : "" ;
                //     html+='<div class="row">'+
                //         '<div class="col-xs-8">'+
                //         '<input type="number" class="final" name="'+question.variable+'" min="'+min+'" max="'+max+'" value="'+defaultValue+'">'+
                //         '</div></div>';

                // }


                // if (scope.removeDialogReady) {
                //     scope.removeDialogReady();
                // }
                // scope.removeDialogReady = scope.$on('DialogReady', function() {
                //     $('#password-modal').dialog('open');
                //     $('#finalized_questions').attr('opacity', 1.0);
                //     // $('#surveyName').focus();
                //     // $('#question_unique_required_chbox').prop('checked' , true);
                // });

                // if (scope.removeSurveyTakerCompleted) {
                //     scope.removeSurveyTakerCompleted();
                // }
                // scope.removeSurveyTakerCompleted = scope.$on('SurveyTakerCompleted', function() {

                //     for(i=0; i<scope.survey_questions.length; i++){

                //         survey_vars[scope.survey_questions[i].variable] = scope[scope.survey_questions[i].variable];
                //     }

                //     Wait('start');
                //     Rest.setUrl(url);
                //     Rest.post(survey_vars)
                //         .success(function(data) {
                //             scope.new_job_id = data.job;
                //             // scope.$emit(callback, data);
                //             $('#password-modal').dialog('close');
                //             scope.$emit('StartPlaybookRun', passwords);
                //         })
                //         .error(function (data, status) {
                //             ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                //                 msg: 'Attempt to start job at ' + url + ' failed. POST returned: ' + status });
                //         });



                // });

            Rest.setUrl(survey_url);
            Rest.get()
                .success(function (data) {
                    if(!Empty(data)){
                        // generator.inject(form, { id: 'password-modal' , mode: 'edit', related: false, scope: scope, breadCrumbs: false });
                        // ShowSurveyModal({ title: data.name, scope: scope, callback: 'DialogReady' , mode: 'survey-taker'});

                        scope.survey_name = data.name;
                        scope.survey_description = data.description;
                        scope.survey_questions = data.spec;

                        // if(!Empty(scope.survey_description)){
                        //     $('#survey_taker_description').append(scope.survey_description);
                        // }

                        for(i=0; i<scope.survey_questions.length; i++){
                            buildHtml(scope.survey_questions[i], i);
                        }
                        // scope.addQuestion();
                        // Wait('stop');
                    } else {
                        // AddSurvey({
                        //     scope: scope
                        // });
                    }

                })
            .error(function (data, status) {
                ProcessErrors(scope, data, status, form, { hdr: 'Error!',
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
            var scope = params.scope,
                id = params.id,
                base = $location.path().replace(/^\//, '').split('/')[0],
                url,
                job_template,
                extra_vars,
                new_job_id,
                new_job,
                launch_url,
                prompt_for_vars = false,
                html,
                passwords;
            scope.job_template_id = id;
            if (base === 'job_templates') {
                url = GetBasePath('job_templates') + id + '/launch/';
            }
            else {
                url = GetBasePath('jobs') + id + '/relaunch/';
            }


            if (scope.removePostTheJob) {
                scope.removePostTheJob();
            }
            scope.removePostTheJob = scope.$on('PostTheJob', function() {
                var url = (job_template.related.jobs) ? job_template.related.jobs : job_template.related.job_template + 'jobs/';
                Wait('start');
                Rest.setUrl(url);
                Rest.post(job_template)
                    .success(function (data) {
                        new_job_id = data.id;
                        launch_url = data.related.start;
                        prompt_for_vars = data.ask_variables_on_launch;
                        new_job = data;
                        if (data.passwords_needed_to_start.length > 0) {
                            scope.$emit('PromptForPasswords', data.passwords_needed_to_start);
                        }
                        else if (data.ask_variables_on_launch) {
                            scope.$emit('PromptForVars');
                        }
                        else {
                            scope.$emit('StartPlaybookRun');
                        }
                    })
                    .error(function (data, status) {
                        var key, html;
                        if (status === 400) {
                            // there's a data problem with the job template
                            html = "<ul style=\"list-style-type: none; margin: 15px 0;\">\n";
                            for (key in data) {
                                html += "<li><strong>" + key + "</strong>: " + data[key][0] + "</li>\n";
                            }
                            html += "</ul>\n";
                            Wait('stop');
                            Alert('Job Template Error', "<p>Fix the following issues before using the template:</p>" + html, 'alert-danger');
                        }
                        else {
                            ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                               msg: 'Failed to create job. POST returned status: ' + status });
                        }
                    });
            });

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
                //var base = $location.path().replace(/^\//, '').split('/')[0];
                $location.path('/jobs/' + data.job);
            });

            if (scope.removeStartPlaybookRun) {
                scope.removeStartPlaybookRun();
            }
            scope.removeStartPlaybookRun = scope.$on('StartPlaybookRun', function() {
                LaunchJob({
                    scope: scope,
                    url: url,
                    callback: 'PlaybookLaunchFinished',
                    passwords: passwords
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
                        callback: 'StartPlaybookRun',
                        url: url,
                        html: html
                    });
                }
                else {
                    // scope.$emit('StartPlaybookRun');
                    CreateLaunchDialog({scope: scope, html: html, url: url});
                }

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
                    new_job_id = data.id;
                    launch_url = url;//data.related.start;
                    scope.passwords_needed_to_start = data.passwords_needed_to_start;
                    scope.prompt_for_vars = data.ask_variables_on_launch;
                    // scope.extra_vars = data.variables_needed_to_start;
                    scope.survey_enabled = data.survey_enabled;

                    // new_job = data;
                    html = '<form class="    ng-valid ng-valid-required" name="job_launch_form" id="job_launch_form" autocomplete="off" nonvalidate>';
                    if (data.passwords_needed_to_start.length > 0) {
                        scope.$emit('PromptForPasswords', data.passwords_needed_to_start, html, url);
                    }
                    else if (data.ask_variables_on_launch) {
                        scope.$emit('PromptForVars', html, url);
                    } else if (data.survey_enabled===true) {
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