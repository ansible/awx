/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

'use strict';

export default
angular.module('JobSubmissionHelper', [ 'RestServices', 'Utilities', 'CredentialFormDefinition', 'CredentialsListDefinition',
'JobSubmissionHelper', 'JobTemplateFormDefinition', 'ModalDialog', 'FormGenerator', 'JobVarsPromptFormDefinition'])

.factory('CreateLaunchDialog', ['$compile', 'CreateDialog', 'Wait', 'ParseTypeChange',
function($compile, CreateDialog, Wait, ParseTypeChange) {
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
      });
    };

  }])

  .factory('PromptForPasswords', ['CredentialForm',
  function(CredentialForm) {
    return function(params) {
      var scope = params.scope,
      callback = params.callback || 'PasswordsAccepted',
      url = params.url,
      form = CredentialForm,
      fld, field,
      html=params.html || "";

      scope.passwords = params.passwords;

      html += "<div class=\"alert alert-info\">Launching this job requires the passwords listed below. Enter and confirm each password before continuing.</div>\n";

      scope.passwords.forEach(function(password) {
        // Prompt for password
        field = form.fields[password];
        fld = password;
        scope[fld] = '';
        html += "<div class=\"form-group prepend-asterisk\">\n";
        html += "<label for=\"" + fld + "\">" + field.label + "</label>\n";
        html += "<input type=\"password\" ";
        html += "ng-model=\"" + fld + '" ';
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

      .factory('CheckPasswords', ['Rest', 'GetBasePath', 'ProcessErrors', 'Empty',
      function(Rest, GetBasePath, ProcessErrors, Empty) {
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

      // Submit SCM Update request
      .factory('ProjectUpdate', ['PromptForPasswords', 'LaunchJob', 'Rest', '$location', 'GetBasePath', 'ProcessErrors', 'Alert', 'Wait',
      function (PromptForPasswords, LaunchJob, Rest, $location, GetBasePath, ProcessErrors, Alert, Wait) {
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
              Alert('Update Started', '<div>The request to start the SCM update process was submitted. ' +
              'To monitor the update status, refresh the page by clicking the <i class="fa fa-refresh"></i> button.</div>', 'alert-info', null, null, null, null, true);
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
    .factory('InventoryUpdate', ['PromptForPasswords', 'LaunchJob', 'Rest', 'GetBasePath', 'ProcessErrors', 'Alert', 'Wait',
    function (PromptForPasswords, LaunchJob, Rest, GetBasePath, ProcessErrors, Alert, Wait) {
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
            Alert('Sync Started', '<div>The request to start the inventory sync process was submitted. ' +
            'To monitor the status refresh the page by clicking the <i class="fa fa-refresh"></i> button.</div>', 'alert-info', null, null, null, null, true);
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
