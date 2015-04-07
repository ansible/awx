/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  JobTemplatesHelper
 *
 *  Routines shared by job related controllers
 *
 */
/**
 * @ngdoc function
 * @name helpers.function:JobTemplatesHelper
 * @description  Routines shared by job related controllers
 */

export default
angular.module('JobTemplatesHelper', ['Utilities'])

/*
 * Add bits to $scope for handling callback url help
 *
 */

.factory('CallbackHelpInit', ['$location', 'GetBasePath', 'Rest', 'JobTemplateForm', 'GenerateForm', '$routeParams', 'LoadBreadCrumbs', 'ProcessErrors', 'ParseTypeChange',
         'ParseVariableString', 'Empty', 'LookUpInit', 'InventoryList', 'CredentialList','ProjectList', 'RelatedSearchInit', 'RelatedPaginateInit', 'Wait',
         function($location, GetBasePath, Rest, JobTemplateForm, GenerateForm, $routeParams, LoadBreadCrumbs, ProcessErrors,ParseTypeChange,
                  ParseVariableString, Empty, LookUpInit, InventoryList, CredentialList, ProjectList, RelatedSearchInit, RelatedPaginateInit, Wait) {
                      return function(params) {

                          var scope = params.scope,
                          defaultUrl = GetBasePath('job_templates'),
                          // generator = GenerateForm,
                          form = JobTemplateForm(),
                          // loadingFinishedCount = 0,
                          // base = $location.path().replace(/^\//, '').split('/')[0],
                          master = {},
                          id = $routeParams.template_id,
                          relatedSets = {};
                          // checkSCMStatus, getPlaybooks, callback,
                          // choicesCount = 0;

                          // The form uses awPopOverWatch directive to 'watch' scope.callback_help for changes. Each time the
                          // popover is activated, a function checks the value of scope.callback_help before constructing the content.
                          scope.setCallbackHelp = function() {
                              scope.callback_help = "<p>With a provisioning callback URL and a host config key a host can contact Tower and request a configuration update using this job " +
                                  "template. The request from the host must be a POST. Here is an example using curl:</p>\n" +
                                  "<pre>curl --data \"host_config_key=" + scope.example_config_key + "\" " +
                                  scope.callback_server_path + GetBasePath('job_templates') + scope.example_template_id + "/callback/</pre>\n" +
                                  "<p>Note the requesting host must be defined in the inventory associated with the job template. If Tower fails to " +
                                  "locate the host, the request will be denied.</p>" +
                                  "<p>Successful requests create an entry on the Jobs page, where results and history can be viewed.</p>";
                          };

                          // The md5 helper emits NewMD5Generated whenever a new key is available
                          if (scope.removeNewMD5Generated) {
                              scope.removeNewMD5Generated();
                          }
                          scope.removeNewMD5Generated = scope.$on('NewMD5Generated', function() {
                              scope.configKeyChange();
                          });

                          // Fired when user enters a key value
                          scope.configKeyChange = function() {
                              scope.example_config_key = scope.host_config_key;
                              scope.setCallbackHelp();
                          };

                          // Set initial values and construct help text
                          scope.callback_server_path = $location.protocol() + '://' + $location.host() + (($location.port()) ? ':' + $location.port() : '');
                          scope.example_config_key = '5a8ec154832b780b9bdef1061764ae5a';
                          scope.example_template_id = 'N';
                          scope.setCallbackHelp();

                          // this fills the job template form both on copy of the job template
                          // and on edit
                          scope.fillJobTemplate  = function(){
                              // id = id || $rootScope.copy.id;
                              // Retrieve detail record and prepopulate the form
                              Rest.setUrl(defaultUrl + id);
                              Rest.get()
                              .success(function (data) {
                                  var fld, i;
                                  LoadBreadCrumbs({ path: '/job_templates/' + id, title: data.name });
                                  for (fld in form.fields) {
                                      if (fld !== 'variables' && data[fld] !== null && data[fld] !== undefined) {
                                          if (form.fields[fld].type === 'select') {
                                              if (scope[fld + '_options'] && scope[fld + '_options'].length > 0) {
                                                  for (i = 0; i < scope[fld + '_options'].length; i++) {
                                                      if (data[fld] === scope[fld + '_options'][i].value) {
                                                          scope[fld] = scope[fld + '_options'][i];
                                                      }
                                                  }
                                              } else {
                                                  scope[fld] = data[fld];
                                              }
                                          } else {
                                              scope[fld] = data[fld];
                                              if(fld ==='survey_enabled'){
                                                  // $scope.$emit('EnableSurvey', fld);
                                                  $('#job_templates_survey_enabled_chbox').attr('checked', scope[fld]);
                                                  if(Empty(data.summary_fields.survey)) {
                                                      $('#job_templates_delete_survey_btn').hide();
                                                      $('#job_templates_edit_survey_btn').hide();
                                                      $('#job_templates_create_survey_btn').show();
                                                  }
                                                  else{
                                                      $('#job_templates_delete_survey_btn').show();
                                                      $('#job_templates_edit_survey_btn').show();
                                                      $('#job_templates_create_survey_btn').hide();
                                                      scope.survey_exists = true;
                                                  }
                                              }
                                          }
                                          master[fld] = scope[fld];
                                      }
                                      if (fld === 'variables') {
                                          // Parse extra_vars, converting to YAML.
                                          scope.variables = ParseVariableString(data.extra_vars);
                                          master.variables = scope.variables;
                                      }
                                      if (form.fields[fld].type === 'lookup' && data.summary_fields[form.fields[fld].sourceModel]) {
                                          scope[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] =
                                              data.summary_fields[form.fields[fld].sourceModel][form.fields[fld].sourceField];
                                          master[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] =
                                              scope[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField];
                                      }
                                  }
                                  Wait('stop');
                                  scope.url = data.url;

                                  scope.ask_variables_on_launch = (data.ask_variables_on_launch) ? 'true' : 'false';
                                  master.ask_variables_on_launch = scope.ask_variables_on_launch;

                                  relatedSets = form.relatedSets(data.related);

                                  if (data.host_config_key) {
                                      scope.example_config_key = data.host_config_key;
                                  }
                                  scope.example_template_id = id;
                                  scope.setCallbackHelp();

                                  scope.callback_url = scope.callback_server_path + ((data.related.callback) ? data.related.callback :
                                                                                     GetBasePath('job_templates') + id + '/callback/');
                                  master.callback_url = scope.callback_url;

                                  scope.can_edit = data.summary_fields.can_edit;

                                  LookUpInit({
                                      scope: scope,
                                      form: form,
                                      current_item: data.inventory,
                                      list: InventoryList,
                                      field: 'inventory',
                                      input_type: "radio"
                                  });

                                  LookUpInit({
                                      url: GetBasePath('credentials') + '?kind=ssh',
                                      scope: scope,
                                      form: form,
                                      current_item: data.credential,
                                      list: CredentialList,
                                      field: 'credential',
                                      hdr: 'Select Machine Credential',
                                      input_type: "radio"
                                  });

                                  LookUpInit({
                                      scope: scope,
                                      form: form,
                                      current_item: data.project,
                                      list: ProjectList,
                                      field: 'project',
                                      input_type: "radio"
                                  });


                                  if(scope.project === "" && scope.playbook === ""){
                                    scope.toggleScanInfo();
                                  }

                                  RelatedSearchInit({
                                      scope: scope,
                                      form: form,
                                      relatedSets: relatedSets
                                  });

                                  RelatedPaginateInit({
                                      scope: scope,
                                      relatedSets: relatedSets
                                  });

                                  scope.$emit('jobTemplateLoaded', data.related.cloud_credential, master);
                              })
                              .error(function (data, status) {
                                  ProcessErrors(scope, data, status, form, {
                                      hdr: 'Error!',
                                      msg: 'Failed to retrieve job template: ' + $routeParams.template_id + '. GET status: ' + status
                                  });
                              });
                          };

                      };
                  }]);
