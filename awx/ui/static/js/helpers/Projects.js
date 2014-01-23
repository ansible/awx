/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  ProjectsHelper
 *
 *  Use GetProjectPath({ scope: <scope>, master: <master obj> }) to 
 *  load scope.project_local_paths (array of options for drop-down) and
 *  scope.base_dir (readonly field). 
 *
 */

angular.module('ProjectsHelper', ['RestServices', 'Utilities', 'ProjectStatusDefinition', 'ProjectFormDefinition'])

    .factory('ProjectStatus', ['$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'GenerateForm', 
        'Prompt', 'ProcessErrors', 'GetBasePath', 'FormatDate', 'ProjectStatusForm', 'Wait',
    function($rootScope, $location, $log, $routeParams, Rest, Alert, GenerateForm, Prompt, ProcessErrors, GetBasePath,
          FormatDate, ProjectStatusForm, Wait) {
    return function(params) {

        var project_id = params.project_id;
        var last_update = params.last_update;
        
        var generator = GenerateForm;
        var form = ProjectStatusForm;
        
        Wait('start');

        // Using jquery dialog for its expandable property
        var html = "<div id=\"status-modal-dialog\"><div id=\"form-container\" style=\"width: 100%;\"></div></div>\n";
        $('#projects-modal-container').empty().append(html);

        var scope = generator.inject(form, { mode: 'edit', id: 'form-container', related: false, breadCrumbs: false });
        generator.reset();

        // Set modal dimensions based on viewport width
        var ww = $(document).width(); 
        var wh = $('body').height();
        var x, y, maxrows;
        if (ww > 1199) {
            // desktop
            x = 675;
            y = (750 > wh) ? wh - 20 : 750;
            maxrows = 20;
        }
        else if (ww <= 1199 && ww >= 768) {
            x = 550;
            y = (620 > wh) ? wh - 15 : 620;
            maxrows = 15;
        }
        else {
            x = (ww - 20);
            y = (500 > wh) ? wh : 500;
            maxrows = 10;
        }
        // Create the modal
        $('#status-modal-dialog').dialog({
            buttons: { "OK": function() {  $( this ).dialog( "close" ); } },
            modal: true, 
            width: x, 
            height: y,
            autoOpen: false,
            create: function (e, ui) {
                // fix the close button
                $('.ui-dialog[aria-describedby="status-modal-dialog"]').find('.ui-dialog-titlebar button').empty().attr({ 'class': 'close' }).text('x'); 
                // fix the OK button
                $('.ui-dialog[aria-describedby="status-modal-dialog"]').find('.ui-dialog-buttonset button:first')
                    .attr({ 'class': 'btn btn-primary' });
                },
            resizeStop: function(e, ui) {
                // for some reason, after resizing dialog the form and fields (the content) doesn't expand to 100%
                var dialog = $('.ui-dialog[aria-describedby="status-modal-dialog"]');
                var content = dialog.find('#status-modal-dialog');
                content.width( dialog.width() - 28 );
                },
            close: function(e, ui) {
                // Destroy on close
                // Destroy on close
                $('.tooltip').each( function(index) {
                    // Remove any lingering tooltip <div> elements
                    $(this).remove();
                    });
                $('.popover').each(function(index) {
                    // remove lingering popover <div> elements
                    $(this).remove();
                    });
                $('#status-modal-dialog').dialog('destroy');
                $('#projects-modal-container').empty();
                },
            open: function(e, ui) {
                Wait('stop');
                }
            });
        
        // Retrieve detail record and prepopulate the form
        Rest.setUrl(last_update);
        Rest.get()
            .success( function(data, status, headers, config) {
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
                $('#status-modal-dialog')
                  .dialog({ title: results.summary_fields.project.name + ' Status'})
                  .dialog('open');
                
                })
            .error( function(data, status, headers, config) {
                $('#form-modal').modal("hide");
                ProcessErrors(scope, data, status, form,
                    { hdr: 'Error!', msg: 'Failed to retrieve status of project: ' + project_id + '. GET status: ' + status });
                });
    }
    }]);

    