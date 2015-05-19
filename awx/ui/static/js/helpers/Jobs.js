/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  JobsHelper
 *
 *  Routines shared by job related controllers
 *
 */
   /**
 * @ngdoc function
 * @name helpers.function:Jobs
 * @description    routines shared by job related controllers
*/

import listGenerator from 'tower/shared/list-generator/main';

export default
    angular.module('JobsHelper', ['Utilities', 'RestServices', 'FormGenerator', 'JobSummaryDefinition', 'InventoryHelper', 'GeneratorHelpers',
        'JobSubmissionHelper', 'LogViewerHelper', 'SearchHelper', 'PaginationHelpers', 'AdhocHelper', listGenerator.name])

    /**
     *  JobsControllerInit({ scope: $scope });
     *
     *  Initialize calling scope with all the bits required to support a jobs list
     *
     */
    .factory('JobsControllerInit', ['$location', 'Find', 'DeleteJob', 'RelaunchJob', 'LogViewer', '$window',
        function($location, Find, DeleteJob, RelaunchJob, LogViewer, $window) {
            return function(params) {
                var scope = params.scope,
                    iterator = (params.iterator) ? params.iterator : scope.iterator;
                    //base = $location.path().replace(/^\//, '').split('/')[0];

                scope.deleteJob = function(id) {
                    DeleteJob({ scope: scope, id: id });
                };

                scope.relaunchJob = function(event, id) {
                    var list, job, typeId;
                    try {
                        $(event.target).tooltip('hide');
                    }
                    catch(e) {
                        //ignore
                    }
                    if (scope.completed_jobs) {
                        list = scope.completed_jobs;
                    }
                    else if (scope.running_jobs) {
                        list = scope.running_jobs;
                    }
                    else if (scope.queued_jobs) {
                        list = scope.queued_jobs;
                    }
                    else if (scope.jobs) {
                        list = scope.jobs;
                    }
                    else if(scope.all_jobs){
                        list = scope.all_jobs;
                    }
                    job = Find({ list: list, key: 'id', val: id });
                    if (job.type === 'inventory_update') {
                        typeId = job.inventory_source;
                    }
                    else if (job.type === 'project_update') {
                        typeId = job.project;
                    }
                    else if (job.type === 'job' || job.type === "system_job" || job.type === 'ad_hoc_command') {
                        typeId = job.id;
                    }
                    RelaunchJob({ scope: scope, id: typeId, type: job.type, name: job.name });
                };

                scope.refreshJobs = function() {
                    // if (base !== 'jobs') {
                        scope.search(iterator);
                    // }

                };

                scope.viewJobLog = function(id) {
                    var list, job;
                    if (scope.completed_jobs) {
                        list = scope.completed_jobs;
                    }
                    else if (scope.running_jobs) {
                        list = scope.running_jobs;
                    }
                    else if (scope.queued_jobs) {
                        list = scope.queued_jobs;
                    }
                    else if (scope.jobs) {
                        list = scope.jobs;
                    }
                    else if(scope.all_jobs){
                        list = scope.all_jobs;
                    }
                    else if(scope.portal_jobs){
                        list=scope.portal_jobs;
                    }
                    job = Find({ list: list, key: 'id', val: id });
                    if (job.type === 'job') {
                        if(scope.$parent.portalMode===true){
                            $window.open('/#/jobs/' + job.id, '_blank');
                        }
                        else {
                            $location.url('/jobs/' + job.id);
                        }
                    } else if (job.type === 'ad_hoc_command') {
                        if(scope.$parent.portalMode===true){
                            $window.open('/#/ad_hoc_commands/' + job.id, '_blank');
                        }
                        else {
                            $location.url('/ad_hoc_commands/' + job.id);
                        }
                    } else {
                        LogViewer({
                            scope: scope,
                            url: job.url
                        });
                    }
                };
            };
        }
    ])

    .factory('RelaunchJob', ['RelaunchInventory', 'RelaunchPlaybook', 'RelaunchSCM', 'RelaunchAdhoc',
        function(RelaunchInventory, RelaunchPlaybook, RelaunchSCM, RelaunchAdhoc) {
            return function(params) {
                var scope = params.scope,
                    id = params.id,
                    type = params.type,
                    name = params.name;
                if (type === 'inventory_update') {
                    RelaunchInventory({ scope: scope, id: id});
                }
                else if (type === 'ad_hoc_command') {
                    RelaunchAdhoc({ scope: scope, id: id, name: name });
                }
                else if (type === 'job' || type === 'system_job') {
                    RelaunchPlaybook({ scope: scope, id: id, name: name });
                }
                else if (type === 'project_update') {
                    RelaunchSCM({ scope: scope, id: id });
                }
            };
        }
    ])

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
        function (Rest, Wait, GetBasePath, FormatDate, ProcessErrors, GenerateForm, JobSummary) {
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


    .factory('JobsListUpdate', ['Rest', function(Rest) {
        return function(params) {
            var scope = params.scope,
                parent_scope = params.parent_scope,
                list = params.list;

            scope[list.name].forEach(function(item, item_idx) {
                var fld, field,
                    itm = scope[list.name][item_idx];

                //if (item.type === 'inventory_update') {
                //    itm.name = itm.name.replace(/^.*?:/,'').replace(/^: /,'');
                //}

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
                //Set the name link
                if (item.type === "inventory_update") {
                    Rest.setUrl(item.related.inventory_source);
                    Rest.get()
                        .success(function(data) {
                            itm.nameHref = "/home/groups?id=" + data.group;
                        });
                }
                else if (item.type === "project_update") {
                    itm.nameHref = "/projects/" + item.project;
                }
                else if (item.type === "job") {
                    itm.nameHref = "";
                }

                if (list.name === 'completed_jobs' || list.name === 'running_jobs') {
                    itm.status_tip = itm.status_label + '. Click for details.';
                }
                else if (list.name === 'queued_jobs') {
                    itm.status_tip = 'Pending';
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
            });
        };
    }])

    /**
     *
     *  Called from JobsList controller to load each section or list on the page
     *
     */
    .factory('LoadJobsScope', ['$routeParams', '$location', '$compile', 'SearchInit', 'PaginateInit', 'generateList', 'JobsControllerInit', 'JobsListUpdate', 'SearchWidget',
        function($routeParams, $location, $compile, SearchInit, PaginateInit, GenerateList, JobsControllerInit, JobsListUpdate, SearchWidget) {
        return function(params) {
            var parent_scope = params.parent_scope,
                scope = params.scope,
                list = params.list,
                id = params.id,
                url = params.url,
                pageSize = params.pageSize || 5,
                base = $location.path().replace(/^\//, '').split('/')[0],
                search_params = params.searchParams,
                spinner = (params.spinner === undefined) ? true : params.spinner,
                e, html, key;

            // Add the search widget. We want it arranged differently, so we're injecting and compiling it separately
            html = SearchWidget({
                iterator: list.iterator,
                template: params.list,
                includeSize: false
            });
            e = angular.element(document.getElementById(id + '-search-container')).append(html);
            $compile(e)(scope);

            GenerateList.inject(list, {
                mode: 'edit',
                id: id,
                breadCrumbs: false,
                scope: scope,
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
                pageSize: pageSize
            });

            scope.iterator = list.iterator;

            if (scope.removePostRefresh) {
                scope.removePostRefresh();
            }
            scope.$on('PostRefresh', function(){
                JobsControllerInit({ scope: scope, parent_scope: parent_scope });
                JobsListUpdate({ scope: scope, parent_scope: parent_scope, list: list });
                parent_scope.$emit('listLoaded');
                // setTimeout(function(){
                //     scope.$apply();
                // }, 300);
            });

            if (base === 'jobs' && list.name === 'completed_jobs') {
                if ($routeParams.id__int) {
                    scope[list.iterator + 'SearchField'] = 'id';
                    scope[list.iterator + 'SearchValue'] = $routeParams.id__int;
                    scope[list.iterator + 'SearchFieldLabel'] = 'Job ID';
                }
            }

            if (search_params) {
                for (key in search_params) {
                    scope[key] = search_params[key];
                }
            }
            scope.search(list.iterator, null, null, null, null, spinner);
        };
    }])

    .factory('DeleteJob', ['Find', 'GetBasePath', 'Rest', 'Wait', 'ProcessErrors', 'Prompt', 'Alert',
    function(Find, GetBasePath, Rest, Wait, ProcessErrors, Prompt, Alert){
        return function(params) {
            var scope = params.scope,
                id = params.id,
                job = params.job,
                callback = params.callback,
                action, jobs, url, action_label, hdr;

            if (!job) {
                if (scope.completed_jobs) {
                    jobs = scope.completed_jobs;
                }
                else if (scope.running_jobs) {
                    jobs = scope.running_jobs;
                }
                else if (scope.queued_jobs) {
                    jobs = scope.queued_jobs;
                }
                else if (scope.all_jobs) {
                    jobs = scope.all_jobs;
                }
                else if (scope.jobs) {
                    jobs = scope.jobs;
                }
                job = Find({list: jobs, key: 'id', val: id });
            }

            if (job.status === 'pending' || job.status === 'running' || job.status === 'waiting') {
                url = job.related.cancel;
                action_label = 'cancel';
                hdr = 'Cancel Job';
            } else {
                url = job.url;
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
                            if (callback) {
                                scope.$emit(callback, action_label);
                            }
                            else {
                                scope.search(scope.iterator);
                            }
                        })
                        .error(function() {
                            Wait('stop');
                            $('#prompt-modal').modal('hide');
                            // Ignore the error. The job most likely already finished.
                            // ProcessErrors(scope, data, status, null, { hdr: 'Error!', msg: 'Call to ' + url +
                            //    ' failed. POST returned status: ' + status });
                        });
                } else {
                    Rest.destroy()
                        .success(function () {
                            $('#prompt-modal').modal('hide');
                            if (callback) {
                                scope.$emit(callback, action_label);
                            }
                            else {
                                scope.search(scope.iterator);
                            }
                        })
                        .error(function () {
                            Wait('stop');
                            $('#prompt-modal').modal('hide');
                            // Ignore the error. The job most likely already finished.
                            //ProcessErrors(scope, data, status, null, { hdr: 'Error!', msg: 'Call to ' + url +
                            //    ' failed. DELETE returned status: ' + status });
                        });
                }
            };

            if (scope.removeCancelNotAllowed) {
                scope.removeCancelNotAllowed();
            }
            scope.removeCancelNotAllowed = scope.$on('CancelNotAllowed', function() {
                Wait('stop');
                Alert('Job Completed', 'The request to cancel the job could not be submitted. The job already completed.', 'alert-info');
            });

            if (scope.removeCancelJob) {
                scope.removeCancelJob();
            }
            scope.removeCancelJob = scope.$on('CancelJob', function() {
                var body;
                body = (action_label === 'cancel' || job.status === 'new') ? "Submit the request to cancel" : "Delete";
                Prompt({
                    hdr: hdr,
                    body: "<div class=\"alert alert-info\">" + body + " job #" + id + " " + job.name  + "?</div>",
                    action: action
                });
            });

            if (action_label === 'cancel') {
                Rest.setUrl(url);
                Rest.get()
                    .success(function(data) {
                        if (data.can_cancel) {
                            scope.$emit('CancelJob');
                        }
                        else {
                            scope.$emit('CancelNotAllowed');
                        }
                    })
                    .error(function(data, status) {
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!', msg: 'Call to ' + url +
                            ' failed. GET returned: ' + status });
                    });
            }
            else {
                scope.$emit('CancelJob');
            }

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
            ProjectUpdate({ scope: scope, project_id: id });
        };
    }])

    .factory('RelaunchAdhoc', ['AdhocRun', function(AdhocRun) {
        return function(params) {
            var scope = params.scope,
                id = params.id;
            AdhocRun({ scope: scope, project_id: id, relaunch: true });
        };
    }]);
