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
        var last_update = params.last_update;
        var generator = GenerateForm;
        var form = ProjectStatusForm;
        var scope;
        
        // Retrieve detail record and prepopulate the form
        Rest.setUrl(last_update);
        Rest.get()
            .success( function(data, status, headers, config) {
                // load up the form
                scope = generator.inject(form, { mode: 'edit', modal: true, related: false});
                generator.reset();
                var results = data;
                for (var fld in form.fields) {
                    if (results[fld]) {
                       if (fld == 'created') {
                          scope[fld] = FormatDate(new Date(results[fld]));
                       }
                       else {
                          scope[fld] = results[fld];
                       }
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
                scope.formModalHeader = results.summary_fields.project.name + '<span class="subtitle"> - SCM Status</span>';
                $('#form-modal .btn-success').removeClass('btn-success').addClass('btn-none');
                $('#form-modal').addClass('skinny-modal');
                if (!scope.$$phase) {
                   scope.$digest();
                }
                })
            .error( function(data, status, headers, config) {
                $('#form-modal').modal("hide");
                ProcessErrors(scope, data, status, form,
                    { hdr: 'Error!', msg: 'Failed to retrieve status of project: ' + project_id + '. GET status: ' + status });
                });
    }
    }]);