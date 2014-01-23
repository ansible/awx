/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  JobsHelper
 *
 *  Routines shared by job related controllers
 *  
 */

angular.module('JobsHelper', ['Utilities', 'FormGenerator', 'JobSummaryDefinition'])

    .factory('JobStatusToolTip', [ function() {
    return function(status) {
        var toolTip;
        switch (status) {
            case 'successful':
            case 'success':
                toolTip = 'There were no failed tasks.';
                break;
            case 'failed':
                toolTip = 'Some tasks encountered errors.';
                break; 
            case 'canceled': 
                toolTip = 'Stopped by user request.';
                break;
            case 'new':
                toolTip = 'In queue, waiting on task manager.';
                break;
            case 'waiting':
                toolTip = 'SCM Update or Inventory Update is executing.';
                break;
            case 'pending':
                toolTip = 'Not in queue, waiting on task manager.';
                break;
            case 'running':
                toolTip = 'Playbook tasks executing.';
                break;
        }
        return toolTip;
        }
        }])

    .factory('ShowJobSummary', ['Rest', 'Wait', 'GetBasePath', 'FormatDate', 'ProcessErrors', 'GenerateForm', 'JobSummary',
    function(Rest, Wait, GetBasePath, FormatDate, ProcessErrors, GenerateForm, JobSummary) {
    return function(params) {
        // Display status info in a modal dialog- called from inventory edit page
        
        var job_id = params.job_id;

        var generator = GenerateForm;
        var form = JobSummary;
        
        // Using jquery dialog for its expandable property
        
        var html = "<div id=\"status-modal-dialog\" title=\"Job " + job_id + "\"><div id=\"form-container\" style=\"width: 100%;\"></div></div>\n";
        
        $('#inventory-modal-container').empty().append(html);
        var scope = generator.inject(form, { mode: 'edit', id: 'form-container', breadCrumbs: false, related: false });
        
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
                $('.tooltip').each( function(index) {
                    // Remove any lingering tooltip <div> elements
                    $(this).remove();
                    });
                $('.popover').each(function(index) {
                    // remove lingering popover <div> elements
                    $(this).remove();
                    });
                $('#status-modal-dialog').dialog('destroy');
                $('#inventory-modal-container').empty();
                },
            open: function(e, ui) {
                Wait('stop');
                }
            });
        
        function calcRows (content) {
            var n = content.match(/\n/g);
            var rows = (n) ? n.length : 1;
            return (rows > maxrows) ? 20 : rows;
            }

        Wait('start');
        var url = GetBasePath('jobs') + job_id + '/';
        Rest.setUrl(url); 
        Rest.get()
            .success( function(data, status, headers, config) {
                scope.id = data.id;
                scope.name = data.name;
                scope.status = data.status; 
                scope.result_stdout = data.result_stdout;
                scope.result_traceback = data.result_traceback;
                scope['stdout_rows'] = calcRows(scope['result_stdout']);
                scope['traceback_rows'] = calcRows(scope['result_traceback']);
                var cDate = new Date(data.created);
                scope.created = FormatDate(cDate);
                $('#status-modal-dialog').dialog('open');
                })
            .error( function(data, status, headers, config) {
                ProcessErrors(scope, data, status, null,
                    { hdr: 'Error!', msg: 'Attempt to load job failed. GET returned status: ' + status });
                });
        }
        }]);

