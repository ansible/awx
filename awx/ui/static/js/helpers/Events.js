/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  EventsHelper
 *
 *  EventView - show the job_events form in a modal dialog
 *
 */
angular.module('EventsHelper', ['RestServices', 'Utilities', 'JobModalEventDefinition'])
.factory('EventView', ['$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'JobModalEventForm', 'GenerateForm', 
         'Prompt', 'ProcessErrors', 'GetBasePath', 'FormatDate',
    function($rootScope, $location, $log, $routeParams, Rest, Alert, JobEventForm, GenerateForm, Prompt, ProcessErrors, GetBasePath,
          FormatDate) {
    return function(params) {
        var event_id = params.event_id;
        var generator = GenerateForm;
        var form = JobEventForm;
        var defaultUrl = GetBasePath('base') + 'job_events/' + event_id + '/';
        var scope = generator.inject(form, { mode: 'edit', modal: true, related: false});
        generator.reset();
        var master = {};
       
        scope.formModalAction = function() {
            $('#form-modal').modal("hide");
            }

        scope.formModalActionLabel = 'OK';
        scope.formModalCancelShow = false;
        
        $('#form-modal .btn-success').removeClass('btn-success').addClass('btn-none');
        
        // Retrieve detail record and prepopulate the form
        Rest.setUrl(defaultUrl);
        Rest.get()
            .success( function(data, status, headers, config) {
                scope.formModalHeader = data['event_display'];
                scope.event_data = JSON.stringify(data['event_data'], null, '\t');
                })
            .error( function(data, status, headers, config) {
                $('#form-modal').modal("hide");
                ProcessErrors(scope, data, status, form,
                    { hdr: 'Error!', msg: 'Failed to retrieve event: ' + event_id + '. GET status: ' + status });
                });
       
        if (!scope.$$phase) {
           scope.$digest();
        }
        
        }
        }]);