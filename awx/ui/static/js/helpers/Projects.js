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

'use strict';

angular.module('ProjectsHelper', ['RestServices', 'Utilities', 'ProjectStatusDefinition', 'ProjectFormDefinition'])

.factory('ProjectStatus', ['$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'GenerateForm',
    'Prompt', 'ProcessErrors', 'GetBasePath', 'FormatDate', 'ProjectStatusForm', 'Wait',
    function ($rootScope, $location, $log, $routeParams, Rest, Alert, GenerateForm, Prompt, ProcessErrors, GetBasePath,
        FormatDate, ProjectStatusForm, Wait) {
        return function (params) {

            var project_id = params.project_id,
                last_update = params.last_update,
                generator = GenerateForm,
                form = ProjectStatusForm,
                html, scope, ww, wh, x, y, maxrows;

            Wait('start');

            html = "<div id=\"status-modal-dialog\"><div id=\"form-container\" style=\"width: 100%;\"></div></div>\n";
            $('#projects-modal-container').empty().append(html);

            scope = generator.inject(form, { mode: 'edit', id: 'form-container', related: false, breadCrumbs: false });
            generator.reset();

            // Set modal dimensions based on viewport width
            ww = $(document).width();
            wh = $('body').height();
            if (ww > 1199) {
                // desktop
                x = 675;
                y = (750 > wh) ? wh - 20 : 750;
                maxrows = 20;
            } else if (ww <= 1199 && ww >= 768) {
                x = 550;
                y = (620 > wh) ? wh - 15 : 620;
                maxrows = 15;
            } else {
                x = (ww - 20);
                y = (500 > wh) ? wh : 500;
                maxrows = 10;
            }
            // Create the modal
            $('#status-modal-dialog').dialog({
                buttons: {
                    "OK": function () {
                        $(this).dialog("close");
                    }
                },
                modal: true,
                width: x,
                height: y,
                autoOpen: false,
                create: function () {
                    // fix the close button
                    $('.ui-dialog[aria-describedby="status-modal-dialog"]').find('.ui-dialog-titlebar button').empty().attr({
                        'class': 'close'
                    }).text('x');
                    // fix the OK button
                    $('.ui-dialog[aria-describedby="status-modal-dialog"]').find('.ui-dialog-buttonset button:first')
                        .attr({
                            'class': 'btn btn-primary'
                        });
                },
                resizeStop: function () {
                    var dialog = $('.ui-dialog[aria-describedby="status-modal-dialog"]'),
                        titleHeight = dialog.find('.ui-dialog-titlebar').outerHeight(),
                        buttonHeight = dialog.find('.ui-dialog-buttonpane').outerHeight(),
                        content = dialog.find('#status-modal-dialog');
                    content.width(dialog.width() - 28);
                    content.css({ height: (dialog.height() - titleHeight - buttonHeight - 10) });
                    
                },
                close: function () {
                    // Destroy on close
                    // Destroy on close
                    $('.tooltip').each(function () {
                        // Remove any lingering tooltip <div> elements
                        $(this).remove();
                    });
                    $('.popover').each(function () {
                        // remove lingering popover <div> elements
                        $(this).remove();
                    });
                    $('#status-modal-dialog').dialog('destroy');
                    $('#projects-modal-container').empty();
                },
                open: function () {
                    Wait('stop');
                }
            });

            // Retrieve detail record and prepopulate the form
            Rest.setUrl(last_update);
            Rest.get()
                .success(function (data) {
                    var results = data, fld;
                    for (fld in form.fields) {
                        if (results[fld]) {
                            if (fld === 'created') {
                                scope[fld] = FormatDate(new Date(results[fld]));
                            } else {
                                scope[fld] = results[fld];
                            }
                        } else {
                            if (results.summary_fields.project[fld]) {
                                scope[fld] = results.summary_fields.project[fld];
                            }
                        }
                    }
                    $('#status-modal-dialog')
                        .dialog({
                            title: results.summary_fields.project.name + ' Status'
                        })
                        .dialog('open');

                })
                .error(function (data, status) {
                    ProcessErrors(scope, data, status, form, { hdr: 'Error!',
                        msg: 'Failed to retrieve project: ' + project_id + '. GET returned: ' + status
                    });
                });
        };
    }
]);