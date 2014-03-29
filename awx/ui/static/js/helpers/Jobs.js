/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  JobsHelper
 *
 *  Routines shared by job related controllers
 *
 */

'use strict';

angular.module('JobsHelper', ['Utilities', 'RestServices', 'FormGenerator', 'JobSummaryDefinition', 'InventoryHelper', 'GeneratorHelpers',
    'JobSubmissionHelper', 'SchedulesHelper'])

.factory('JobStatusToolTip', [
    function () {
        return function (status) {
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
        };
    }
])

.factory('ShowJobSummary', ['Rest', 'Wait', 'GetBasePath', 'FormatDate', 'ProcessErrors', 'GenerateForm', 'JobSummary',
    'WatchInventoryWindowResize',
    function (Rest, Wait, GetBasePath, FormatDate, ProcessErrors, GenerateForm, JobSummary, WatchInventoryWindowResize) {
        return function (params) {
            // Display status info in a modal dialog- called from inventory edit page

            var job_id = params.job_id,
                generator = GenerateForm,
                form = JobSummary,
                scope, ww, wh, x, y, maxrows, url, html;

            html = '<div id=\"status-modal-dialog\" title=\"Job ' + job_id + '\">' +
                '<div id=\"form-container\" style=\"width: 100%;\"></div></div>\n';

            $('#inventory-modal-container').empty().append(html);
            
            scope = generator.inject(form, { mode: 'edit', id: 'form-container', breadCrumbs: false, related: false });

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
                    'OK': function () {
                        $(this).dialog('close');
                    }
                },
                modal: true,
                width: x,
                height: y,
                autoOpen: false,
                closeOnEscape: false,
                create: function () {
                    // fix the close button
                    $('.ui-dialog[aria-describedby="status-modal-dialog"]').find('.ui-dialog-titlebar button')
                        .empty().attr({
                            'class': 'close'
                        }).text('x');
                    // fix the OK button
                    $('.ui-dialog[aria-describedby="status-modal-dialog"]').find('.ui-dialog-buttonset button:first')
                        .attr({
                            'class': 'btn btn-primary'
                        });
                },
                resizeStop: function () {
                    // for some reason, after resizing dialog the form and fields (the content) doesn't expand to 100%
                    var dialog = $('.ui-dialog[aria-describedby="status-modal-dialog"]'),
                        titleHeight = dialog.find('.ui-dialog-titlebar').outerHeight(),
                        buttonHeight = dialog.find('.ui-dialog-buttonpane').outerHeight(),
                        content = dialog.find('#status-modal-dialog');
                    content.width(dialog.width() - 28);
                    content.css({ height: (dialog.height() - titleHeight - buttonHeight - 10) });
                },
                close: function () {
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
                    $('#inventory-modal-container').empty();
                    WatchInventoryWindowResize();
                },
                open: function () {
                    Wait('stop');
                }
            });

            function calcRows(content) {
                var n = content.match(/\n/g),
                    rows = (n) ? n.length : 1;
                return (rows > maxrows) ? 20 : rows;
            }

            Wait('start');
            url = GetBasePath('jobs') + job_id + '/';
            Rest.setUrl(url);
            Rest.get()
                .success(function (data) {
                    var cDate;
                    scope.id = data.id;
                    scope.name = data.name;
                    scope.status = data.status;
                    scope.result_stdout = data.result_stdout;
                    scope.result_traceback = data.result_traceback;
                    scope.stdout_rows = calcRows(scope.result_stdout);
                    scope.traceback_rows = calcRows(scope.result_traceback);
                    cDate = new Date(data.created);
                    scope.created = FormatDate(cDate);
                    $('#status-modal-dialog').dialog('open');
                })
                .error(function (data, status) {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Attempt to load job failed. GET returned status: ' + status });
                });
        };

    }
])

/**
 * 
 *  Called from JobsList controller to load each section or list on the page
 *
 */
.factory('LoadScope', ['SearchInit', 'PaginateInit', 'GenerateList', 'PageRangeSetup', 'ProcessErrors', 'Rest',
    function(SearchInit, PaginateInit, GenerateList) {
    return function(params) {
        var parent_scope = params.parent_scope,
            scope = params.scope,
            list = params.list,
            id = params.id,
            url = params.url;

        GenerateList.inject(list, {
            mode: 'edit',
            id: id,
            breadCrumbs: false,
            scope: scope,
            searchSize: 'col-lg-4 col-md-6 col-sm-12 col-xs-12',
            showSearch: true
        });

        SearchInit({
            scope: scope,
            set: list.name,
            list: list,
            url: url
        });

        PaginateInit({
            scope: scope,
            list: list,
            url: url,
            pageSize: 10
        });

        scope.iterator = list.iterator;

        if (scope.removePostRefresh) {
            scope.removePostRefresh();
        }
        scope.$on('PostRefresh', function(){

            scope[list.name].forEach(function(item, item_idx) {
                var fld, field,
                    itm = scope[list.name][item_idx];

                // Set the item type label
                if (list.fields.type) {
                    parent_scope.type_choices.every(function(choice) {
                        if (choice.value === item.type) {
                            itm.type_label = choice.label;
                            return false;
                        }
                        return true;
                    });
                }
                // Set the job status label
                parent_scope.status_choices.every(function(status) {
                    if (status.value === item.status) {
                        itm.status_label = status.label;
                        return false;
                    }
                    return true;
                });
                
                if (list.name === 'completed_jobs' || list.name === 'running_jobs') {
                    itm.status_tip = itm.status_label + '. Click for details.';
                }
                else if (list.name === 'queued_jobs') {
                    itm.status_tip = 'Pending';
                }
                else if (list.name === 'scheduled_jobs') {
                    itm.enabled = (itm.enabled) ? true : false;
                    itm.play_tip = (itm.enabled) ? 'Schedule is Active. Click to temporarily stop.' : 'Schedule is temporarily stopped. Click to activate.';
                }

                // Copy summary_field values
                for (field in list.fields) {
                    fld = list.fields[field];
                    if (fld.sourceModel) {
                        if (itm.summary_fields[fld.sourceModel]) {
                            itm[field] = itm.summary_fields[fld.sourceModel][fld.sourceField];
                        }
                    }
                }

                itm.status_popover_title = itm.status_label;
                itm.status_popover = "<p>" + itm.job_explanation + "</p>\n" +
                    "<p><a href=\"/#/jobs/" + itm.id + "\">More...</a></p>\n" +
                    "<div class=\"popover-footer\"><span class=\"key\">esc</span> or click to close</div>\n";
            });
            parent_scope.$emit('listLoaded');
        });
        scope.search(list.iterator);
    };
}])

.factory('DeleteJob', ['Find', 'GetBasePath', 'Rest', 'Wait', 'ProcessErrors', 'Prompt',
function(Find, GetBasePath, Rest, Wait, ProcessErrors, Prompt){
    return function(params) {
        
        var scope = params.scope,
            id = params.id,
            action, jobs, job, url, action_label, hdr;

        if (scope.completed_jobs) {
            jobs = scope.completed_jobs;
        }
        else if (scope.running_jobs) {
            jobs = scope.running_jobs;
        }
        else if (scope.queued_jobs) {
            jobs = scope.queued_jobs;
        }
        job = Find({list: jobs, key: 'id', val: id });

        if (job.status === 'pending' || job.status === 'running' || job.status === 'waiting') {
            url = job.related.cancel;
            action_label = 'cancel';
            hdr = 'Cancel Job';
        } else {
            url = GetBasePath('jobs') + id + '/';
            action_label = 'delete';
            hdr = 'Delete Job';
        }

        action = function () {
            Wait('start');
            Rest.setUrl(url);
            if (action_label === 'cancel') {
                Rest.post()
                    .success(function () {
                        $('#prompt-modal').modal('hide');
                        scope.search(scope.iterator);
                    })
                    .error(function (data, status) {
                        $('#prompt-modal').modal('hide');
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!', msg: 'Call to ' + url +
                            ' failed. POST returned status: ' + status });
                    });
            } else {
                Rest.destroy()
                    .success(function () {
                        $('#prompt-modal').modal('hide');
                        scope.search(scope.iterator);
                    })
                    .error(function (data, status) {
                        $('#prompt-modal').modal('hide');
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!', msg: 'Call to ' + url +
                            ' failed. DELETE returned status: ' + status });
                    });
            }
        };

        Prompt({
            hdr: hdr,
            body: "<div class=\"alert alert-info\">Are you sure you want to " + action_label + " job " + id + " <em>" + job.name  + "</em>?</div>",
            action: action
        });

    };
}])

.factory('RelaunchInventory', ['Find', 'Wait', 'Rest', 'InventoryUpdate', 'ProcessErrors', 'GetBasePath',
function(Find, Wait, Rest, InventoryUpdate, ProcessErrors, GetBasePath) {
    return function(params) {
        var scope = params.scope,
            id = params.id,
            url = GetBasePath('inventory_sources') + id + '/';
        Wait('start');
        Rest.setUrl(url);
        Rest.get()
            .success(function (data) {
                InventoryUpdate({
                    scope: scope,
                    url: data.related.update,
                    group_name: data.summary_fields.group.name,
                    group_source: data.source,
                    tree_id: null,
                    group_id: data.group
                });
            })
            .error(function (data, status) {
                ProcessErrors(scope, data, status, null, { hdr: 'Error!', msg: 'Failed to retrieve inventory source: ' +
                    url + ' GET returned: ' + status });
            });
    };
}])

.factory('RelaunchPlaybook', ['PlaybookRun', function(PlaybookRun) {
    return function(params) {
        var scope = params.scope,
            id = params.id;
        PlaybookRun({ scope: scope, id: id });
    };
}])

.factory('RelaunchSCM', ['ProjectUpdate', function(ProjectUpdate) {
    return function(params) {
        var scope = params.scope,
            id = params.id;
        ProjectUpdate({ scope: scope, id: id });
    };
}])

.factory('ScheduledJobEdit', ['Find', 'EditSchedule', 'GetBasePath', function(Find, EditSchedule, GetBasePath) {
    return function(params) {
        var scope = params.scope,
            id = params.id,
            url = GetBasePath('schedules'),
            schedule = Find({ list: scope.scheduled_jobs, key: 'id', val: id });
        EditSchedule({ scope: scope, schedule: schedule, url: url });
    };
}]);

