/************************************
 * Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *
 *  Jobs.js
 *
 *  Controller functions for the Job model.
 *
 */
/* global jsyaml:false */
'use strict';

function JobsListCtrl($scope, $rootScope, $location, $log, $routeParams, Rest, Alert, JobList, GenerateList, LoadBreadCrumbs, Prompt,
    SearchInit, PaginateInit, ReturnToCaller, ClearScope, ProcessErrors, GetBasePath, LookUpInit, SubmitJob, FormatDate, Refresh,
    JobStatusToolTip, Empty, Wait) {

    ClearScope('htmlTemplate');

    var list = JobList,
        defaultUrl = GetBasePath('jobs'),
        view = GenerateList,
        scope = view.inject(list, { mode: 'edit' }),
        opt;

    $rootScope.flashMessage = null;
    scope.selected = [];

    if (scope.removePostRefresh) {
        scope.removePostRefresh();
    }
    scope.removePostRefresh = scope.$on('PostRefresh', function () {
        var i, cDate;
        $("tr.success").each(function () {
            // Make sure no rows have a green background
            var ngc = $(this).attr('ng-class');
            scope[ngc] = "";
        });
        if (scope.jobs && scope.jobs.length) {
            for (i = 0; i < scope.jobs.length; i++) {
                // Convert created date to local time zone
                cDate = new Date(scope.jobs[i].created);
                scope.jobs[i].created = FormatDate(cDate);
                // Set tooltip and link
                scope.jobs[i].statusBadgeToolTip = JobStatusToolTip(scope.jobs[i].status) +
                    " Click to view status details.";
                scope.jobs[i].statusLinkTo = '/#/jobs/' + scope.jobs[i].id;
            }
        }
    });


    if ($routeParams.job_host_summaries__host) {
        defaultUrl += '?job_host_summaries__host=' + $routeParams.job_host_summaries__host;
    } else if ($routeParams.inventory__int && $routeParams.status) {
        defaultUrl += '?inventory__int=' + $routeParams.inventory__int + '&status=' +
            $routeParams.status;
    }
    SearchInit({
        scope: scope,
        set: 'jobs',
        list: list,
        url: defaultUrl
    });
    PaginateInit({
        scope: scope,
        list: list,
        url: defaultUrl
    });

    // Called from Inventories page, failed jobs link. Find jobs for selected inventory.
    if ($routeParams.inventory__int) {
        scope[list.iterator + 'SearchField'] = 'inventory';
        scope[list.iterator + 'SearchValue'] = $routeParams.inventory__int;
        scope[list.iterator + 'SearchFieldLabel'] = 'Inventory ID';
    }
    if ($routeParams.id__int) {
        scope[list.iterator + 'SearchField'] = 'id';
        scope[list.iterator + 'SearchValue'] = $routeParams.id__int;
        scope[list.iterator + 'SearchFieldLabel'] = 'Job ID';
    }
    if ($routeParams.status) {
        scope[list.iterator + 'SearchField'] = 'status';
        scope[list.iterator + 'SelectShow'] = true;
        scope[list.iterator + 'SearchSelectOpts'] = list.fields.status.searchOptions;
        scope[list.iterator + 'SearchFieldLabel'] = list.fields.status.label.replace(/<br>/g, ' ');
        for (opt in list.fields.status.searchOptions) {
            if (list.fields.status.searchOptions[opt].value === $routeParams.status) {
                scope[list.iterator + 'SearchSelectValue'] = list.fields.status.searchOptions[opt];
                break;
            }
        }
    }

    scope.search(list.iterator);

    LoadBreadCrumbs();

    scope.refresh = function () {
        Wait('start');
        scope.jobLoading = false;
        Refresh({
            scope: scope,
            set: 'jobs',
            iterator: 'job',
            url: scope.current_url
        });
    };

    scope.refreshJob = scope.refresh;

    scope.editJob = function (id, name) {
        LoadBreadCrumbs({
            path: '/jobs/' + id,
            title: id + ' - ' + name
        });
        $location.path($location.path() + '/' + id);
    };

    scope.viewEvents = function (id, name) {
        LoadBreadCrumbs({
            path: '/jobs/' + id,
            title: id + ' - ' + name
        });
        $location.path($location.path() + '/' + id + '/job_events');
    };

    scope.viewSummary = function (id, name) {
        LoadBreadCrumbs({
            path: '/jobs/' + id,
            title: id + ' - ' + name
        });
        $location.path($location.path() + '/' + id + '/job_host_summaries');
    };

    scope.deleteJob = function (id) {
        Rest.setUrl(defaultUrl + id + '/');
        Rest.get()
            .success(function (data) {

                var action, url, action_label, hdr;

                if (data.status === 'pending' || data.status === 'running' || data.status === 'waiting') {
                    url = data.related.cancel;
                    action_label = 'cancel';
                    hdr = 'Cancel Job';
                } else {
                    url = defaultUrl + id + '/';
                    action_label = 'delete';
                    hdr = 'Delete Job';
                }

                action = function () {
                    Rest.setUrl(url);
                    if (action_label === 'cancel') {
                        Rest.post()
                            .success(function () {
                                $('#prompt-modal').modal('hide');
                                scope.search(list.iterator);
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
                                scope.search(list.iterator);
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
                    body: 'Are you sure you want to ' + action_label + ' job ' + id + '?',
                    action: action
                });
            })
            .error(function (data, status) {
                ProcessErrors(scope, data, status, null, { hdr: 'Error!', msg: 'Failed to get job details. GET returned status: ' + status });
            });
    };

    scope.submitJob = function (id, template) {
        SubmitJob({
            scope: scope,
            id: id,
            template: template
        });
    };
}

JobsListCtrl.$inject = ['$scope', '$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'JobList',
    'GenerateList', 'LoadBreadCrumbs', 'Prompt', 'SearchInit', 'PaginateInit', 'ReturnToCaller', 'ClearScope',
    'ProcessErrors', 'GetBasePath', 'LookUpInit', 'SubmitJob', 'FormatDate', 'Refresh', 'JobStatusToolTip',
    'Empty', 'Wait'
];


function JobsEdit($scope, $rootScope, $compile, $location, $log, $routeParams, JobForm, GenerateForm, Rest, Alert, ProcessErrors,
    LoadBreadCrumbs, RelatedSearchInit, RelatedPaginateInit, ReturnToCaller, ClearScope, InventoryList, CredentialList,
    ProjectList, LookUpInit, PromptPasswords, GetBasePath, md5Setup, FormatDate, JobStatusToolTip, Wait) {

    ClearScope('htmlTemplate'); //Garbage collection. Don't leave behind any listeners/watchers from the prior
    //scope.

    var defaultUrl = GetBasePath('jobs'),
        generator = GenerateForm,
        form = JobForm,
        scope = generator.inject(form, {
            mode: 'edit',
            related: true
        }),
        master = {},
        id = $routeParams.id,
        relatedSets = {},
        loadingFinishedCount = 0;

    generator.reset();

    scope.job_id = id;
    scope.parseType = 'yaml';
    scope.statusSearchSpin = false;

    function getPlaybooks(project) {
        if (project !== null && project !== '' && project !== undefined) {
            var url = GetBasePath('projects') + project + '/playbooks/';
            Rest.setUrl(url);
            Rest.get()
                .success(function (data) {
                    scope.playbook_options = [];
                    for (var i = 0; i < data.length; i++) {
                        scope.playbook_options.push(data[i]);
                    }
                    scope.$emit('jobTemplateLoadFinished');
                })
                .error(function () {
                    scope.$emit('jobTemplateLoadFinished');
                });
        } else {
            scope.$emit('jobTemplateLoadFinished');
        }
    }


    // Retrieve each related set and populate the playbook list
    if (scope.jobLoadedRemove) {
        scope.jobLoadedRemove();
    }
    scope.jobLoadedRemove = scope.$on('jobLoaded', function (e, related_cloud_credential) {

        getPlaybooks(scope.project);

        scope[form.name + 'ReadOnly'] = (scope.status === 'new') ? false : true;

        $('#forks-slider').slider("option", "value", scope.forks);
        $('#forks-slider').slider("disable");
        $('input[type="checkbox"]').attr('disabled', 'disabled');
        $('input[type="radio"]').attr('disabled', 'disabled');
        $('#host_config_key-gen-btn').attr('disabled', 'disabled');
        $('textarea').attr('readonly', 'readonly');

        // Get job template and display/hide host callback fields
        Rest.setUrl(scope.template_url);
        Rest.get()
            .success(function (data) {
                var dft = (data.host_config_key) ? 'true' : 'false';
                scope.host_config_key = data.host_config_key;
                md5Setup({
                    scope: scope,
                    master: master,
                    check_field: 'allow_callbacks',
                    default_val: dft
                });
                scope.callback_url = (data.related) ? data.related.callback : '<< Job template not found >>';
                scope.$emit('jobTemplateLoadFinished');
            })
            .error(function () {
                Wait('stop');
                scope.callback_url = '<< Job template not found >>';
            });

        if (related_cloud_credential) {
            //Get the name of the cloud credential
            Rest.setUrl(related_cloud_credential);
            Rest.get()
                .success(function (data) {
                    scope.cloud_credential_name = data.name;
                    scope.$emit('jobTemplateLoadFinished');
                })
                .error(function (data, status) {
                    ProcessErrors(scope, data, status, null, {
                        hdr: 'Error!',
                        msg: 'Failed to related cloud credential. GET returned status: ' + status
                    });
                });
        } else {
            scope.$emit('jobTemplateLoadFinished');
        }
    });

    // Turn off 'Wait' after both cloud credential and playbook list come back
    if (scope.removeJobTemplateLoadFinished) {
        scope.removeJobTemplateLoadFinished();
    }
    scope.removeJobTemplateLoadFinished = scope.$on('jobTemplateLoadFinished', function () {
        loadingFinishedCount++;
        if (loadingFinishedCount >= 3) {
            // The initial template load finished. Now load related jobs, which 
            // will turn off the 'working' spinner.
            Wait('stop');
        }
    });

    // Our job type options
    scope.job_type_options = [{
        value: 'run',
        label: 'Run'
    }, {
        value: 'check',
        label: 'Check'
    }];
    scope.verbosity_options = [{
        value: '0',
        label: 'Default'
    }, {
        value: '1',
        label: 'Verbose'
    }, {
        value: '3',
        label: 'Debug'
    }];
    scope.playbook_options = null;
    scope.playbook = null;

    function calcRows(content) {
        var n = content.match(/\n/g),
            rows = (n) ? n.length : 1;
        return (rows > 15) ? 15 : rows;
    }

    // Retrieve detail record and prepopulate the form
    Wait('start');
    Rest.setUrl(defaultUrl + ':id/');
    Rest.get({ params: { id: id } })
        .success(function (data) {
            //LoadBreadCrumbs({ path: '/jobs/' + id, title: data.id + ' - ' + data.summary_fields.job_template.name });
            var i, cDate, fld, json_obj, related, set;
            LoadBreadCrumbs();
            for (fld in form.fields) {
                if (fld !== 'variables' && data[fld] !== null && data[fld] !== undefined) {
                    if (form.fields[fld].type === 'select') {
                        if (scope[fld + '_options'] && scope[fld + '_options'].length > 0) {
                            for (i = 0; i < scope[fld + '_options'].length; i++) {
                                if (data[fld] === scope[fld + '_options'][i].value) {
                                    scope[fld] = scope[fld + '_options'][i];
                                }
                            }
                        } else {
                            scope[fld] = data[fld];
                        }
                    }
                } else {
                    scope[fld] = data[fld];
                }
                master[fld] = scope[fld];
            }

            scope.id = data.id;
            scope.name = (data.summary_fields && data.summary_fields.job_template) ? data.summary_fields.job_template.name : '';

            if (fld === 'variables') {
                // Parse extra_vars, converting to YAML.  
                if ($.isEmptyObject(data.extra_vars) || data.extra_vars === "{}" || data.extra_vars === "null" ||
                    data.extra_vars === "" || data.extra_vars === null) {
                    scope.variables = "---";
                } else {
                    json_obj = JSON.parse(data.extra_vars);
                    scope.variables = jsyaml.safeDump(json_obj);
                }
                master.variables = scope.variables;
            }
            if (form.fields[fld].type === 'lookup' && data.summary_fields[form.fields[fld].sourceModel]) {
                scope[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] =
                    data.summary_fields[form.fields[fld].sourceModel][form.fields[fld].sourceField];
                master[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] =
                    scope[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField];
            }

            for (fld in form.statusFields) {
                if (data[fld] !== null && data[fld] !== undefined) {
                    if (fld === 'created') {
                        // Convert created date to local time zone 
                        cDate = new Date(data.created);
                        scope.created = FormatDate(cDate);
                    } else {
                        scope[fld] = data[fld];
                    }
                }
            }

            scope.statusToolTip = JobStatusToolTip(data.status);

            $('form[name="jobs_form"] input[type="text"], form[name="jobs_form"] jobs_form textarea').attr('readonly', 'readonly');
            $('form[name="jobs_form"] select').prop('disabled', 'disabled');
            $('form[name="jobs_form"] .lookup-btn').prop('disabled', 'disabled');
            $('form[name="jobs_form"] .buttons, form[name="jobs_form"] hr').hide();

            scope.url = data.url;
            related = data.related;
            for (set in form.related) {
                if (related[set]) {
                    relatedSets[set] = {
                        url: related[set],
                        iterator: form.related[set].iterator
                    };
                }
            }

            scope.stdout_rows = calcRows(scope.result_stdout);

            scope.traceback_rows = calcRows(scope.result_traceback);

            LookUpInit({
                scope: scope,
                form: form,
                current_item: data.inventory,
                list: InventoryList,
                field: 'inventory'
            });

            LookUpInit({
                scope: scope,
                form: form,
                current_item: data.credential,
                list: CredentialList,
                field: 'credential'
            });

            LookUpInit({
                scope: scope,
                form: form,
                current_item: data.project,
                list: ProjectList,
                field: 'project'
            });

            // Initialize related search functions. Doing it here to make sure relatedSets object is populated.
            RelatedSearchInit({
                scope: scope,
                form: form,
                relatedSets: relatedSets
            });
            RelatedPaginateInit({
                scope: scope,
                relatedSets: relatedSets
            });
            scope.template_url = data.related.job_template;
            scope.$emit('jobLoaded', data.related.cloud_credential);
        })
        .error(function (data, status) {
            ProcessErrors(scope, data, status, form, {
                hdr: 'Error!',
                msg: 'Failed to retrieve job: ' + $routeParams.id + '. GET status: ' + status
            });
        });

    scope.refresh = function () {
        Wait('start');
        Rest.setUrl(defaultUrl + id + '/');
        Rest.get()
            .success(function (data) {
                scope.status = data.status;
                scope.result_stdout = data.result_stdout;
                scope.result_traceback = data.result_traceback;
                scope.stdout_rows = calcRows(scope.result_stdout);
                scope.traceback_rows = calcRows(scope.result_traceback);
                Wait('stop');
            })
            .error(function (data, status) {
                Wait('stop');
                ProcessErrors(scope, data, status, null, {
                    hdr: 'Error!',
                    msg: 'Attempt to load job failed. GET returned status: ' + status
                });
            });
    };

    scope.jobSummary = function () {
        $location.path('/jobs/' + id + '/job_host_summaries');
    };

    scope.jobEvents = function () {
        $location.path('/jobs/' + id + '/job_events');
    };
}

JobsEdit.$inject = ['$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'JobForm',
    'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'RelatedSearchInit', 'RelatedPaginateInit',
    'ReturnToCaller', 'ClearScope', 'InventoryList', 'CredentialList', 'ProjectList', 'LookUpInit', 'PromptPasswords',
    'GetBasePath', 'md5Setup', 'FormatDate', 'JobStatusToolTip', 'Wait'
];
