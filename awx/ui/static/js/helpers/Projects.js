/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  ProjectsHelper
 *
 *  Use GetProjectPath({ scope: <scope>, master: <master obj> }) to 
 *  load scope.project_local_paths (array of options for drop-down) and
 *  scope.base_dir (readonly field). 
 *
 */

angular.module('ProjectsHelper', ['RestServices', 'Utilities', 'ProjectStatusDefinition'])
.factory('ProjectStatus', ['$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'GenerateForm', 
         'Prompt', 'ProcessErrors', 'GetBasePath', 'FormatDate', 'ProjectStatusForm',
    function($rootScope, $location, $log, $routeParams, Rest, Alert, GenerateForm, Prompt, ProcessErrors, GetBasePath,
          FormatDate, ProjectStatusForm) {
    return function(params) {

        var project_id = params.project_id;
        var generator = GenerateForm;
        var form = ProjectStatusForm;
        var scope;
        var defaultUrl = GetBasePath('projects') + project_id + '/project_updates/';
        
        // Retrieve detail record and prepopulate the form
        Rest.setUrl(defaultUrl);
        Rest.get()
            .success( function(data, status, headers, config) {
                // load up the form
                if (data.results.length > 0) {
                    scope = generator.inject(form, { mode: 'edit', modal: true, related: false});
                    generator.reset();
                    var results = data.results[data.results.length - 1];  //get the latest
                    for (var fld in form.fields) {
                        if (results[fld]) {
                           scope[fld] = results[fld];
                        }
                        else {
                           if (results.summary_fields.project[fld]) {
                              scope[fld] = results.summary_fields.project[fld]
                           }
                        }
                    }
                    scope.formModalAction = function() {
                        $('#form-modal').modal("hide");
                        }
                    scope.formModalActionLabel = 'OK';
                    scope.formModalCancelShow = false;
                    scope.formModalInfo = false;
                    $('#form-modal .btn-success').removeClass('btn-success').addClass('btn-none');
                    $('#form-modal').addClass('skinny-modal');
                    if (!scope.$$phase) {
                        scope.$digest();
                    }
                }
                else {
                    Alert('No Updates Available', 'There is no SCM update information available for this project. An update has not yet been ' +
                        ' completed.  If you have not already done so, start an update for this project.', 'alert-info');
                }
                })
            .error( function(data, status, headers, config) {
                $('#form-modal').modal("hide");
                ProcessErrors(scope, data, status, form,
                    { hdr: 'Error!', msg: 'Failed to retrieve status of project: ' + project_id + '. GET status: ' + status });
                });
    }
    }]);