/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

   /**
 * @ngdoc function
 * @name helpers.function:Jobs
 * @description    routines shared by job related controllers
*/

import listGenerator from '../shared/list-generator/main';

export default
    angular.module('JobsHelper', ['Utilities', 'RestServices', 'FormGenerator', 'JobSummaryDefinition', 'InventoryHelper', 'GeneratorHelpers',
        'JobSubmissionHelper', 'StandardOutHelper', 'AdhocHelper', listGenerator.name])

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

    .factory('JobsListUpdate', [function() {
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

    .factory('DeleteJob', ['Find', 'GetBasePath', 'Rest', 'Wait',
    'ProcessErrors', 'Prompt', 'Alert', '$filter',
    function(Find, GetBasePath, Rest, Wait, ProcessErrors, Prompt, Alert,
        $filter){
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
                hdr = 'Cancel';
            } else {
                url = job.url;
                action_label = 'delete';
                hdr = 'Delete';
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
                                // @issue: OLD SEARCH
                                // scope.search(scope.iterator);
                            }
                        })
                        .error(function(obj, status) {
                            Wait('stop');
                            $('#prompt-modal').modal('hide');
                            if (status === 403) {
                                Alert('Error', obj.detail);
                            }
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
                                // @issue: OLD SEARCH
                                // scope.search(scope.iterator);
                            }
                        })
                        .error(function (obj, status) {
                            Wait('stop');
                            $('#prompt-modal').modal('hide');
                            if (status === 403) {
                                Alert('Error', obj.detail);
                            }
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
                var cancelBody = "<div class=\"Prompt-bodyQuery\">Submit the request to cancel?</div>";
                var deleteBody = "<div class=\"Prompt-bodyQuery\">Are you sure you want to delete the job below?</div><div class=\"Prompt-bodyTarget\">#" + id + " " + $filter('sanitize')(job.name)  + "</div>";
                Prompt({
                    hdr: hdr,
                    body: (action_label === 'cancel' || job.status === 'new') ? cancelBody : deleteBody,
                    action: action,
                    actionText: (action_label === 'cancel' || job.status === 'new') ? "YES" : "DELETE"
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

    .factory('RelaunchPlaybook', ['InitiatePlaybookRun', function(InitiatePlaybookRun) {
        return function(params) {
            var scope = params.scope,
                id = params.id;
            InitiatePlaybookRun({ scope: scope, id: id, relaunch: true });
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
