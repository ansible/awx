/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  JobsHelper
 *
 *  Routines shared by job related controllers
 *
 */

'use strict';

angular.module('JobsHelper', ['Utilities', 'FormGenerator', 'JobSummaryDefinition', 'InventoryHelper'])

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
                    content = dialog.find('#status-modal-dialog');
                    content.width(dialog.width() - 28);
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
    function(SearchInit, PaginateInit, GenerateList, PageRangeSetup, ProcessErrors, Rest) {
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
            showSearch: false
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

        
        // The following bits probably don't belong here once the API is available.

        if (scope.removePostRefresh) {
            scope.removePostRefresh();
        }
        scope.$on('PostRefresh', function(e, data){
            var i, modifier;
            PageRangeSetup({
                scope: scope,
                count: data.count,
                next: data.next,
                previous: data.previous,
                iterator: list.iterator
            });
            scope[list.iterator + 'Loading'] = false;
            for (i = 1; i <= 3; i++) {
                modifier = (i === 1) ? '' : i;
                scope[list.iterator + 'HoldInput' + modifier] = false;
            }
            scope[list.name] = data.results;
            window.scrollTo(0, 0);

            scope[list.name].forEach(function(item, item_idx) {
                // Set the item type label
                if (list.fields.type) {
                    parent_scope.type_choices.every(function(choice) {
                        if (choice.value === item.type) {
                            scope[list.name][item_idx].type = choice.label;
                            return false;
                        }
                        return true;
                    });
                }
                // Set the job status label
                parent_scope.status_choices.every(function(status) {
                    if (status.value === item.status) {
                        scope[list.name][item_idx].status_label = status.label;
                        return false;
                    }
                    return true;
                });
                if (list.name === 'completed_jobs' || list.name === 'running_jobs') {
                    scope[list.name][item_idx].status_tip = scope[list.name][item_idx].status_label + '. Click for details.';
                }
                else {
                    scope[list.name][item_idx].status_tip = 'Pending';
                }
                scope[list.name][item_idx].status_popover_title = scope[list.name][item_idx].status_label;
                scope[list.name][item_idx].status_popover = "<p>" + scope[list.name][item_idx].job_explanation + "</p>\n";
                scope[list.name][item_idx].status_popover += "<p><a href=\"/#/jobs/" + scope[list.name][item_idx].id + "\">More...</a></p>\n";
            });

            parent_scope.$emit('listLoaded');
        });

        Rest.setUrl(url);
        Rest.get()
            .success(function(data) {
                scope.$emit('PostRefresh', data);
            })
            .error(function(data, status) {
                ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                    msg: 'Call to ' + url + ' failed. GET returned: ' + status });
            });
    };
}]);