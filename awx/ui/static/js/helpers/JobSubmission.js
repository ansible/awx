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
* The JobSubmission.js file handles launching a job via a playbook run. There is a workflow that is involved in gathering all the
* variables needed to launch a job, including credentials, passwords, extra variables, and survey data. Depending on what information
* is needed to launch the job, a modal is built that prompts the user for any required information. This modal is built by creating
* an html string with all the fields necessary to launch the job. This html string then gets compiled and opened in a dialog modal.
*
* #Workflow when user hits launch button
*
* A 'get' call is made to the API's 'job_templates/:job_template_id/launch' endpoint for that job template. The response from the API will specify
*
*```
*    "credential_needed_to_start": true,
*    "can_start_without_user_input": false,
*    "ask_variables_on_launch": false,
*    "passwords_needed_to_start": [],
*    "variables_needed_to_start": [],
*    "survey_enabled": false
*```
* #Step 1a - Check if there is a credential included in the job template: PromptForCredential
*
* The first step is to check if a credential was specified in the job template, by looking at the value of `credential_needed_to_start` .
* If this boolean is true, then that means that the user did NOT specify a credential in the job template and we must prompt them to select a credential.
* This emits a call to `PromptForCredential` which will do a lookup on the credentials endpoint and show a modal window with the list
* of credentials for the user to choose from.
*
* #Step 1b - Check if the credential requires a password: CheckPasswords
*
* The second part of this process is to check if the credential the user picks requires a prompt for a password. A call is made (in the `CheckPasswords` factory)
* to the chosen credential
* and checks if ``password: ASK`` , ``become_password:ASK`` , or ``vault_password: ASK``. If any of these are ASK, then we begin building the html string for
* each required password (see step 2). If none of these require a password, then we contine on to prompting for vars (see step 3)
*
* #Step 2 - Build password html string: PromptForPasswords
*
* We may detect from the inital 'get' call that we may need to prompt the user for passwords. The ``passwords_needed_to_start`` array from the 'get' call
* will explictly tell us which passwords we must prompt for.  Alternatively, we may have found that in steps 1a and 1b that
* we have must prompt for passwords. Either way, we arrive in `PromptForPasswords` factory which builds the html string depending on how the particular credential is setup.
*
* #Step 3 - extra vars text editor: PromptForVars
*
* We may arrive at step three if the credential selected does not require a password, or if the password html string is already done being built.
* if ``ask_variables_on_launch`` was true in the inital 'get' call, then we build the extra_vars text editor in the `PromptForVars` factory.
* This factory makes a REST call to the job template and finds if any 'extra_vars' were specified in the job template. It takes any specified
* extra vars and includes them in the extra_vars text editor that is built in the same factory. This code is added to the html string and passed along
* to the next step.
*
* #Step 4 - Survey Taker: PromptForSurvey
*
* The last step in building the job submission modal is building the survey taker. If ``survey_enabled`` is true from the initial 'get' call,
* we make a REST call to the survey endpoint for the specified job and gather the survey data. The `PromptForSurvey` factory takes the survey
* data and adds to the html string any various survey question.
*
* #Step 5 - build the modal: CreateLaunchDialog
*
* At this point, we need to compile our giant html string onto the modal and open the job submission modal. This happens in the `CreateLaunch`
* factory. In this factory the 'Launch' button for the job is tied to the validity of the form, which handles the validation of these fields.
*
* #Step 6 - Launch the job: LaunchJob
*
* This is maybe the most crucial step. We have setup everything we need in order to gather information from the user and now we want to be sure
* we handle it correctly. And there are many scenarios to take into account. The first scenario we check for is is ``survey_enabled=true`` and
*  ``prompt_for_vars=false``, in which case we want to make sure to include the extra_vars from the job template in the data being
* sent to the API (it is important to note that anything specified in the extra vars on job submission will override vars specified in the job template.
* Likewise, any variables specified in the extra vars that are duplicated by the survey vars, will get overridden by the survey vars).
* If the previous scenario is NOT the case, then we continue to gather the modal's answers regularly: gather the passwords, then the extra_vars, then
* any survey results. Also note that we must gather any required survey answers, as well as any optional survey answers that happened to be provided
* by the user. We also include the credential that was chosen if the user was prompted to select a credential.
* At this point we have all the info we need and we are almost ready to perform a POST to the '/launch' endpoint. We must lastly check
* if the user was not prompted for anything and therefore we don't want to pass any extra_vars to the POST. Once this is done we
* make the REST POST call and provide all the data to hte API. The response from the API will be the job ID, which is used to redirect the user
* to the job detail page for that job run.
*
* @Usage
* This is usage information.
*/

'use strict';

export default
angular.module('JobSubmissionHelper', [ 'RestServices', 'Utilities', 'CredentialFormDefinition', 'CredentialsListDefinition',
'LookUpHelper', 'JobSubmissionHelper', 'JobTemplateFormDefinition', 'ModalDialog', 'FormGenerator', 'JobVarsPromptFormDefinition'])

.factory('LaunchJob', ['Rest', 'Wait', 'ProcessErrors', 'ToJSON', 'Empty', 'GetBasePath',
function(Rest, Wait, ProcessErrors, ToJSON, Empty, GetBasePath) {
  return function(params) {
    var scope = params.scope,
    callback = params.callback || 'JobLaunched',
    job_launch_data = {},
    url = params.url,
    vars_url = GetBasePath('job_templates')+scope.job_template_id + '/',
    // fld,
    extra_vars;

    //found it easier to assume that there will be extra vars, and then check for a blank object at the end
    job_launch_data.extra_vars = {};

    //gather the extra vars from the job template if survey is enabled and prompt for vars is false
    if (scope.removeGetExtraVars) {
      scope.removeGetExtraVars();
    }
    scope.removeGetExtraVars = scope.$on('GetExtraVars', function() {

      Rest.setUrl(vars_url);
      Rest.get()
      .success(function (data) {
        if(!Empty(data.extra_vars)){
          data.extra_vars = ToJSON('yaml',  data.extra_vars, false);
          $.each(data.extra_vars, function(key,value){
            job_launch_data.extra_vars[key] = value;
          });
        }
        scope.$emit('BuildData');
      })
      .error(function (data, status) {
        ProcessErrors(scope, data, status, { hdr: 'Error!',
        msg: 'Failed to retrieve job template extra variables.'  });
      });
    });

    //build the data object to be sent to the job launch endpoint. Any variables gathered from the survey and the extra variables text editor are inserted into the extra_vars dict of the job_launch_data
    if (scope.removeBuildData) {
      scope.removeBuildData();
    }
    scope.removeBuildData = scope.$on('BuildData', function() {
      if(!Empty(scope.passwords_needed_to_start) && scope.passwords_needed_to_start.length>0){
        scope.passwords.forEach(function(password) {
          job_launch_data[password] = scope[password];
          scope.passwords_needed_to_start.push(password+'_confirm'); // i'm pushing these values into this array for use during the survey taker parsing
        });
      }
      if(scope.prompt_for_vars===true){
        extra_vars = ToJSON(scope.parseType, scope.extra_vars, false);
        if(!Empty(extra_vars)){
          $.each(extra_vars, function(key,value){
            job_launch_data.extra_vars[key] = value;
          });
        }

      }

      if(scope.survey_enabled===true){
        for (var i=0; i < scope.survey_questions.length; i++){
          var fld = scope.survey_questions[i].variable;
          // grab all survey questions that have answers
          if(scope.survey_questions[i].required || (scope.survey_questions[i].required === false && scope[fld].toString()!=="")) {
            job_launch_data.extra_vars[fld] = scope[fld];
          }
          // for optional text and text-areas, submit a blank string if min length is 0
          if(scope.survey_questions[i].required === false && (scope.survey_questions[i].type === "text" || scope.survey_questions[i].type === "textarea") && scope.survey_questions[i].min === 0 && (scope[fld] === "" || scope[fld] === undefined)){
            job_launch_data.extra_vars[fld] = "";
          }
        }
      }

      // include the credential used if the user was prompted to choose a cred
      if(!Empty(scope.credential)){
        job_launch_data.credential_id = scope.credential;
      }

      // If the extra_vars dict is empty, we don't want to include it if we didn't prompt for anything.
      if(jQuery.isEmptyObject(job_launch_data.extra_vars)===true && scope.prompt_for_vars===false){
        delete job_launch_data.extra_vars;
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
        msg: 'Failed updating job ' + scope.job_template_id + ' with variables. POST returned: ' + status });
      });
    });

    // if the user has a survey and does not have 'prompt for vars' selected, then we want to
    // include the extra vars from the job template in the job launch. so first check for these conditions
    // and then overlay any survey vars over those.
    if(scope.prompt_for_vars===false && scope.survey_enabled===true){
      scope.$emit('GetExtraVars');
    }
    else {
      scope.$emit('BuildData');
    }


  };
}])

.factory('PromptForCredential', ['$location', 'Wait', 'GetBasePath', 'LookUpInit', 'JobTemplateForm', 'CredentialList', 'Rest', 'Prompt', 'ProcessErrors',
    'CheckPasswords',
function($location, Wait, GetBasePath, LookUpInit, JobTemplateForm, CredentialList, Rest, Prompt, ProcessErrors, CheckPasswords) {
  return function(params) {

    var scope = params.scope,
    selectionMade;

    Wait('stop');
    scope.credential = '';

    if (scope.removeShowLookupDialog) {
      scope.removeShowLookupDialog();
    }
    scope.removeShowLookupDialog = scope.$on('ShowLookupDialog', function() {
      selectionMade = function () {
        // scope.$emit(callback, scope.credential);
        CheckPasswords({
            scope: scope,
            credential: scope.credential,
            callback: 'ContinueCred'
        });
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
      $('#password-modal').find('#job_extra_vars').before(scope.helpContainer);
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
        "job_launch_form." + fld + ".$error.required\">Please enter a password.</div>\n";
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
          "job_launch_form." + fld + ".$error.required\">Please confirm the password.</span>\n";
          html += (field.awPassMatch) ? "<span class=\"error\" ng-show=\"job_launch_form." + fld +
          ".$error.awpassmatch\">This value does not match the password you entered previously.  Please confirm that password.</div>\n" : "";
          html += "<div class=\"error api-error\" ng-bind=\"" + fld + "_api_error\"></div>\n";
          html += "</div>\n";
        }
      });

      scope.$emit(callback, html, url);

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
          "<blockquote>---<br />somevar: somevalue<br />password: magic<br /></blockquote>\n";

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
          minlength, maxlength,
          checked, min, max,
          survey_url = GetBasePath('job_templates') + id + '/survey_spec/' ;

          function buildHtml(question, index){
            question.index = index;
            question.question_name = question.question_name.replace(/</g, "&lt;");
            question.question_name = question.question_name.replace(/>/g, "&gt;");
            question.question_description = (question.question_description) ? question.question_description.replace(/</g, "&lt;") : undefined;
            question.question_description = (question.question_description) ? question.question_description.replace(/>/g, "&gt;") : undefined;


            requiredAsterisk = (question.required===true) ? "prepend-asterisk" : "";
            requiredClasses = (question.required===true) ? "ng-pristine ng-invalid-required ng-invalid" : "";

            html+='<div id="taker_'+question.index+'" class="form-group '+requiredAsterisk+' ">';
            html += '<label for="'+question.variable+'">'+question.question_name+'</label>\n';

            if(!Empty(question.question_description)){
              html += '<div class="survey_taker_description"><i>'+question.question_description+'</i></div>\n';
            }

            // if(question.default && question.default.indexOf('<') !== -1){
            //     question.default = (question.default) ? question.default.replace(/</g, "&lt;") : undefined;
            // }
            // if (question.default && question.default.indexOf('>') !== -1){
            //     question.default = (question.default) ? question.default.replace(/>/g, "&gt;") : undefined;
            // }
            scope[question.variable] = question.default;

            if(question.type === 'text' ){
              minlength = (!Empty(question.min)) ? Number(question.min) : "";
              maxlength =(!Empty(question.max)) ? Number(question.max) : "" ;
              html+='<input type="text" id="'+question.variable+'" ng-model="'+question.variable+'" '+
              'name=" '+question.variable+' " ' +
              'ng-minlength="'+minlength+'" ng-maxlength="'+maxlength+'" '+
              'class="form-control" ng-required='+question.required+'>'+
              '<div class="error survey_error" ng-show="job_launch_form.'+ question.variable + '.$dirty && ' +
              'job_launch_form.'+question.variable+'.$error.required\">Please enter an answer.</div>'+
              '<div class="error survey_error" ng-show="job_launch_form.'+ question.variable + '.$error.minlength || ' +
              'job_launch_form.'+question.variable+'.$error.maxlength\">Please enter an answer between {{'+minlength+'}} to {{'+maxlength+'}} characters long.</div>'+
              '<div class=\"error api-error\" ng-bind=\"" + fld + "_api_error\"></div>';
            }

            if(question.type === "textarea"){
              scope[question.variable] = (question.default_textarea) ? question.default_textarea : (question.default) ? question.default : "";
              minlength = (!Empty(question.min)) ? Number(question.min) : "";
              maxlength =(!Empty(question.max)) ? Number(question.max) : "" ;
              html+='<textarea id="'+question.variable+'" name="'+question.variable+'" ng-model="'+question.variable+'" '+
              'ng-minlength="'+minlength+'" ng-maxlength="'+maxlength+'" '+
              'class="form-control final"  ng-required="'+question.required+'" rows="3"></textarea>'+
              '<div class="error survey_error" ng-show="job_launch_form.'+ question.variable + '.$dirty && ' +
              'job_launch_form.'+question.variable+'.$error.required\">Please enter an answer.</div>'+
              '<div class="error survey_error" ng-show="job_launch_form.'+ question.variable + '.$error.minlength || ' +
              'job_launch_form.'+question.variable+'.$error.maxlength\">Please enter an answer between {{'+minlength+'}} to {{'+maxlength+'}} characters long.</div>'+
              '<div class=\"error api-error\" ng-bind=\"" + fld + "_api_error\"></div>';
            }
            if(question.type === 'password' ){
              minlength = (!Empty(question.min)) ? Number(question.min) : "";
              maxlength =(!Empty(question.max)) ? Number(question.max) : "" ;
              html+='<input type="password" id="'+question.variable+'_password" ng-model="'+question.variable+'" '+
              'name=" '+question.variable+' " ' +
              'ng-hide="'+question.variable+'_pwcheckbox" ' +
              'ng-minlength="'+minlength+'" ng-maxlength="'+maxlength+'" '+
              'class="form-control" ng-required='+question.required+'>'+
              '<div class="error survey_error" ng-show="job_launch_form.'+ question.variable + '.$dirty && ' +
              'job_launch_form.'+question.variable+'.$error.required\">Please enter an answer.</div>'+
              '<div class="error survey_error" ng-show="job_launch_form.'+ question.variable + '.$error.minlength || ' +
              'job_launch_form.'+question.variable+'.$error.maxlength\">Please enter an answer between {{'+minlength+'}} to {{'+maxlength+'}} characters long.</div>'+
              '<div class=\"error api-error\" ng-bind=\"" + fld + "_api_error\"></div>';
              html+='<input type="text" id="'+question.variable+'_text" ng-model="'+question.variable+'" '+
              'name=" '+question.variable+' " ' +
              'ng-show="'+question.variable+'_pwcheckbox"'+
              'ng-minlength="'+minlength+'" ng-maxlength="'+maxlength+'" '+
              'class="form-control" ng-required='+question.required+'>'+
              '<div class="error survey_error" ng-show="job_launch_form.'+ question.variable + '.$dirty && ' +
              'job_launch_form.'+question.variable+'.$error.required\">Please enter an answer.</div>'+
              '<div class="error survey_error" ng-show="job_launch_form.'+ question.variable + '.$error.minlength || ' +
              'job_launch_form.'+question.variable+'.$error.maxlength\">Please enter an answer between {{'+minlength+'}} to {{'+maxlength+'}} characters long.</div>'+
              '<div class=\"error api-error\" ng-bind=\"" + fld + "_api_error\"></div>';
              html+= '<label style="font-weight:normal"><input type="checkbox" ng-model="'+question.variable+'_pwcheckbox" name="pwcheckbox" id="'+question.variable+'_pwcheckbox" ng-checked="false"> <span>Show Password</span></label>';

            }
            if(question.type === 'multiplechoice'){
              choices = question.choices.split(/\n/);
              element = (question.type==="multiselect") ? "checkbox" : 'radio';
              question.default = (question.default) ? question.default : (question.default_multiselect) ? question.default_multiselect : "" ;
              html+='<div class="survey_taker_input" > ';
              for( j = 0; j<choices.length; j++){
                checked = (!Empty(question.default) && question.default.indexOf(choices[j])!==-1) ? "checked" : "";
                choices[j]  = choices[j].replace(/</g, "&lt;");
                choices[j]  = choices[j].replace(/>/g, "&gt;");
                html+= '<input  type="'+element+'" class="mc" ng-model="'+question.variable+'" ng-required="'+question.required+'" name="'+question.variable+ ' " id="'+question.variable+'" value=" '+choices[j]+' " '+checked+' >' +
                '<span>'+choices[j] +'</span><br>' ;
              }
              html+=  '<div class="error survey_error" ng-show="job_launch_form.'+ question.variable + '.$dirty && ' +
              'job_launch_form.'+question.variable+'.$error.required\">Please select an answer.</div>'+
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
              '<div class="error survey_error" ng-show="job_launch_form.'+question.variable+'.$error.checkbox">Please select at least one answer.</div>';
            }

            if(question.type === 'integer'){
              min = (!Empty(question.min)) ? Number(question.min) : "";
              max = (!Empty(question.max)) ? Number(question.max) : "" ;
              html+='<input type="number" id="'+question.variable+'" ng-model="'+question.variable+'" class="form-control" name="'+question.variable+'" ng-required="'+question.required+'"  integer aw-min="'+min+'"  aw-max="'+max+'" />'+
              '<div class="error survey_error" ng-show="job_launch_form.'+ question.variable + '.$dirty && job_launch_form.'+question.variable+'.$error.required">Please enter an answer.</div>'+
              '<div class="error survey_error" ng-show="job_launch_form.'+question.variable+'.$error.number || job_launch_form.'+question.variable+'.$error.integer" >Please enter an answer that is a valid integer.</div>'+
              '<div class="error survey_error" ng-show="job_launch_form.'+question.variable+'.$error.awMin || job_launch_form.'+question.variable+'.$error.awMax">Please enter an answer between {{'+min+'}} and {{'+max+'}}.</div>';

            }

            if(question.type === "float"){
              min = (!Empty(question.min)) ? question.min : "";
              max = (!Empty(question.max)) ? question.max : "" ;
              defaultValue = (!Empty(question.default)) ? question.default : (!Empty(question.default_float)) ? question.default_float : "" ;
              html+='<input type="number" id="'+question.variable+'" ng-model="'+question.variable+'"  class=" form-control" name="'+question.variable+'" ng-required="'+question.required+'" smart-float aw-min="'+min+'"  aw-max="'+max+'"/>'+
              '<div class="error survey_error" ng-show="job_launch_form.'+ question.variable + '.$dirty && job_launch_form.'+question.variable+'.$error.required">Please enter an answer.</div>'+
              '<div class="error survey_error" ng-show="job_launch_form.'+question.variable+'.$error.number || job_launch_form.'+question.variable+'.$error.float">Please enter an answer that is a decimal number.</div>'+
              '<div class="error survey_error" ng-show="job_launch_form.'+question.variable+'.$error.awMin || job_launch_form.'+question.variable+'.$error.awMax">Please enter a decimal number between {{'+min+'}} and {{'+max+'}}.</div>';
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

      .factory('CheckPasswords', ['$compile', 'Rest', 'GetBasePath', 'TextareaResize', 'CreateLaunchDialog', 'GenerateForm', 'JobVarsPromptForm', 'Wait',
      'ParseVariableString', 'ToJSON', 'ProcessErrors', '$routeParams', 'Empty',
      function($compile, Rest, GetBasePath, TextareaResize,CreateLaunchDialog, GenerateForm, JobVarsPromptForm, Wait,
        ParseVariableString, ToJSON, ProcessErrors, $routeParams, Empty) {
          return function(params) {
            var scope = params.scope,
            callback = params.callback,
            credential = params.credential;

            var passwords = [];
            if (!Empty(credential)) {
              Rest.setUrl(GetBasePath('credentials')+credential);
              Rest.get()
              .success(function (data) {
                if(data.kind === "ssh"){
                  if(data.password === "ASK" ){
                    passwords.push("ssh_password");
                  }
                  if(data.ssh_key_unlock === "ASK"){
                    passwords.push("ssh_key_unlock");
                  }
                  if(data.become_password === "ASK"){
                    passwords.push("become_password");
                  }
                  if(data.vault_password === "ASK"){
                    passwords.push("vault_password");
                  }
                }
                scope.$emit(callback, passwords);
              })
              .error(function (data, status) {
                ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                msg: 'Failed to get job template details. GET returned status: ' + status });
              });
            }

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
            if (base === 'job_templates' || base === 'portal' || base === 'inventories') {
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


            if (scope.removeContinueCred) {
              scope.removeContinueCred();
            }
            scope.removeContinueCred = scope.$on('ContinueCred', function(e, passwords) {
                if(passwords.length>0){
                  scope.passwords_needed_to_start = passwords;
                  scope.$emit('PromptForPasswords', passwords, html, url);
                }
                else if (scope.ask_variables_on_launch){
                  scope.$emit('PromptForVars', html, url);
                }
                else if (!Empty(scope.survey_enabled) &&  scope.survey_enabled===true) {
                  scope.$emit('PromptForSurvey', html, url);
                }
                else {
                  scope.$emit('StartPlaybookRun', url);
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
              scope.variables_needed_to_start = data.variables_needed_to_start;
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
