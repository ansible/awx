/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  HostsHelper
 *
 *  Routines that handle host add/edit/delete on the Inventory detail page.
 *
 */

/* jshint loopfunc: true */
   /**
 * @ngdoc function
 * @name helpers.function:Hosts
 * @description    Routines that handle host add/edit/delete on the Inventory detail page.
*/



angular.module('HostsHelper', [ 'RestServices', 'Utilities', 'ListGenerator', 'HostListDefinition',
                                'SearchHelper', 'PaginationHelpers', 'ListGenerator', 'AuthService', 'HostsHelper',
                                'InventoryHelper', 'RelatedSearchHelper', 'InventoryFormDefinition', 'SelectionHelper',
                                'HostGroupsFormDefinition', 'VariablesHelper', 'ModalDialog', 'LogViewerHelper',
                                'GroupListDefinition'
                                ])

.factory('SetEnabledMsg', [ function() {
    return function(host) {
        if (host.has_inventory_sources) {
            // Inventory sync managed, so not clickable
            host.enabledToolTip = (host.enabled) ? 'Host is available' : 'Host is not available';
        }
        else {
            // Clickable
            host.enabledToolTip = (host.enabled) ? 'Host is available. Click to toggle.' : 'Host is not available. Click to toggle.';
        }
    };
}])

.factory('SetHostStatus', ['SetEnabledMsg', function(SetEnabledMsg) {
    return function(host) {
        // Set status related fields on a host object
        host.activeFailuresLink = '/#/hosts/' + host.id + '/job_host_summaries/?inventory=' + host.inventory +
            '&host_name=' + encodeURI(host.name);
        if (host.has_active_failures === true) {
            host.badgeToolTip = 'Most recent job failed. Click to view jobs.';
            host.active_failures = 'failed';
        }
        else if (host.has_active_failures === false && host.last_job === null) {
            host.has_active_failures = 'none';
            host.badgeToolTip = "No job data available.";
            host.active_failures = 'n/a';
        }
        else if (host.has_active_failures === false && host.last_job !== null) {
            host.badgeToolTip = "Most recent job successful. Click to view jobs.";
            host.active_failures = 'success';
        }

        host.enabled_flag = host.enabled;
        SetEnabledMsg(host);

    };
}])

.factory('SetStatus', ['$filter', 'SetEnabledMsg', 'Empty', function($filter, SetEnabledMsg, Empty) {
    return function(params) {

        var scope = params.scope,
            host = params.host,
            i, html, title;

        function ellipsis(a) {
            if (a.length > 25) {
                return a.substr(0,25) + '...';
            }
            return a;
        }

        function noRecentJobs() {
            title = 'No job data';
            html = "<p>No recent job data available for this host.</p>\n";
        }

        function setMsg(host) {
            var j, job, jobs;

            if (host.has_active_failures === true || (host.has_active_failures === false && host.last_job !== null)) {
                if (host.has_active_failures === true) {
                    host.badgeToolTip = 'Most recent job failed. Click to view jobs.';
                    host.active_failures = 'error';
                }
                else {
                    host.badgeToolTip = "Most recent job successful. Click to view jobs.";
                    host.active_failures = 'successful';
                }
                if (host.summary_fields.recent_jobs.length > 0) {
                    // build html table of job status info
                    jobs = host.summary_fields.recent_jobs.sort(
                        function(a,b) {
                            // reverse numerical order
                            return -1 * (a - b);
                        });
                    title = "Recent Jobs";
                    html = "<table class=\"table table-condensed flyout\" style=\"width: 100%\">\n";
                    html += "<thead>\n";
                    html += "<tr>\n";
                    html += "<th>Status</th>\n";
                    html += "<th>Finished</th>\n";
                    html += "<th>Name</th>\n";
                    html += "</tr>\n";
                    html += "</thead>\n";
                    html += "<tbody>\n";
                    for (j=0; j < jobs.length; j++) {
                        job = jobs[j];
                        html += "<tr>\n";

                        html += "<td><a href=\"#/jobs/" + job.id + "\" " +
                            "aw-tool-tip=\"" + job.status.charAt(0).toUpperCase() + job.status.slice(1) +
                            ". Click for details\" data-placement=\"top\"><i class=\"fa icon-job-" +
                            job.status + "\"></i></a></td>\n";

                        html += "<td>" + ($filter('date')(job.finished,'MM/dd HH:mm:ss')).replace(/ /,'<br />') + "</td>\n";

                        html += "<td class=\"break\"><a href=\"#/jobs/" + job.id + "\" " +
                            "aw-tool-tip=\"" + job.status.charAt(0).toUpperCase() + job.status.slice(1) +
                            ". Click for details\" data-placement=\"top\">" + ellipsis(job.name) + "</a></td>\n";

                        html += "</tr>\n";
                    }
                    html += "</tbody>\n";
                    html += "</table>\n";
                }
                else {
                    noRecentJobs();
                }
            }
            else if (host.has_active_failures === false && host.last_job === null) {
                host.badgeToolTip = "No job data available.";
                host.active_failures = 'none';
                noRecentJobs();
            }
            host.job_status_html = html;
            host.job_status_title = title;
        }

        if (!Empty(host)) {
            // update single host
            setMsg(host);
            SetEnabledMsg(host);
        }
        else {
            // update all hosts
            for (i=0; i < scope.hosts.length; i++) {
                setMsg(scope.hosts[i]);
                SetEnabledMsg(scope.hosts[i]);
            }
        }

    };
}])

.factory('ViewJob', ['LogViewer', 'GetBasePath', function(LogViewer, GetBasePath) {
    return function(params) {
        var scope = params.scope,
            id = params.id;
        LogViewer({
            scope: scope,
            url: GetBasePath('jobs') + id + '/'
        });
    };
}])

.factory('HostsReload', [ '$routeParams', 'Empty', 'InventoryHosts', 'GetBasePath', 'SearchInit', 'PaginateInit', 'Wait',
    'SetHostStatus', 'SetStatus', 'ApplyEllipsis', 'SetContainerHeights', 'GetHostContainerRows',
function($routeParams, Empty, InventoryHosts, GetBasePath, SearchInit, PaginateInit, Wait, SetHostStatus, SetStatus,
    ApplyEllipsis, SetContainerHeights) {
    return function(params) {

        var scope = params.scope,
            parent_scope = params.parent_scope,
            group_id = params.group_id,
            inventory_id = params.inventory_id,
            list = InventoryHosts,
            pageSize = (params.pageSize) ? params.pageSize : 20,

            url = ( !Empty(group_id) ) ? GetBasePath('groups') + group_id + '/all_hosts/' :
                GetBasePath('inventory') + inventory_id + '/hosts/';

        scope.search_place_holder='Search ' + scope.selected_group_name;

        if (scope.removeHostsReloadPostRefresh) {
            scope.removeHostsReloadPostRefresh();
        }
        scope.removeHostsReloadPostRefresh = scope.$on('PostRefresh', function(e, set) {
            if (set === 'hosts') {
                for (var i=0; i < scope.hosts.length; i++) {
                    //Set tooltip for host enabled flag
                    scope.hosts[i].enabled_flag = scope.hosts[i].enabled;
                }
                SetStatus({ scope: scope });
                setTimeout(function() { ApplyEllipsis('#hosts_table .host-name a'); }, 2500);
                Wait('stop');
                if (parent_scope) {
                    parent_scope.$emit('HostReloadComplete');
                }
            }
        });

        // Size containers based on viewport
        SetContainerHeights({ scope: scope, reloadHosts: false });

        SearchInit({ scope: scope, set: 'hosts', list: list, url: url });
        PaginateInit({ scope: scope, list: list, url: url, pageSize: pageSize });

        if ($routeParams.host_name) {
            scope[list.iterator + 'InputDisable'] = false;
            scope[list.iterator + 'SearchValue'] = $routeParams.host_name;
            scope[list.iterator + 'SearchField'] = 'name';
            scope[list.iterator + 'SearchFieldLabel'] = list.fields.name.label;
            scope[list.iterator + 'SearchSelectValue'] = null;
        }

        if (scope.show_failures) {
            scope[list.iterator + 'InputDisable'] = true;
            scope[list.iterator + 'SearchValue'] = 'true';
            scope[list.iterator + 'SearchField'] = 'has_active_failures';
            scope[list.iterator + 'SearchFieldLabel'] = list.fields.has_active_failures.label;
            scope[list.iterator + 'SearchSelectValue'] = { value: 1 };
        }
        scope.search(list.iterator, null, true);
    };
}])

.factory('InjectHosts', ['GenerateList', 'InventoryHosts', 'HostsReload',
function(GenerateList, InventoryHosts, HostsReload) {
    return function(params) {

        var group_scope = params.group_scope,
            host_scope = params.host_scope,
            inventory_id = params.inventory_id,
            group_id = params.group_id,
            pageSize = params.pageSize,
            generator = GenerateList;

        // Inject the list html
        generator.inject(InventoryHosts, { scope: host_scope, mode: 'edit', id: 'hosts-container', breadCrumbs: false, searchSize: 'col-lg-6 col-md-6 col-sm-6' });

        // Load data
        HostsReload({ scope: host_scope, group_id: group_id, inventory_id: inventory_id, parent_scope: group_scope, pageSize: pageSize });
    };
}])

.factory('ToggleHostEnabled', [ 'GetBasePath', 'Rest', 'Wait', 'ProcessErrors', 'Alert', 'Find', 'SetEnabledMsg',
function(GetBasePath, Rest, Wait, ProcessErrors, Alert, Find, SetEnabledMsg) {
    return function(params) {

        var id = params.host_id,
            external_source = params.external_source,
            parent_scope = params.parent_scope,
            host_scope = params.host_scope,
            host;

        function setMsg(host) {
            host.enabled = (host.enabled) ? false : true;
            host.enabled_flag = host.enabled;
            SetEnabledMsg(host);
        }

        if (!external_source) {
            // Host is not managed by an external source
            Wait('start');
            host = Find({ list: host_scope.hosts, key: 'id', val: id });
            setMsg(host);

            Rest.setUrl(GetBasePath('hosts') + id + '/');
            Rest.put(host)
                .success( function() {
                    Wait('stop');
                })
                .error( function(data, status) {
                    // Flip the enabled flag back
                    setMsg(host);
                    ProcessErrors(parent_scope, data, status, null,
                        { hdr: 'Error!', msg: 'Failed to update host. PUT returned status: ' + status });
                });
        }
        else {
            Alert('Action Not Allowed', 'This host is managed by an external cloud source. Disable it at the external source, ' +
                'then run an inventory sync to update Tower with the new status.', 'alert-info');
        }
    };
}])

.factory('HostsList', ['$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'HostList', 'GenerateList',
    'Prompt', 'SearchInit', 'PaginateInit', 'ProcessErrors', 'GetBasePath', 'HostsAdd', 'HostsReload', 'SelectionInit',
function($rootScope, $location, $log, $routeParams, Rest, Alert, HostList, GenerateList, Prompt, SearchInit,
    PaginateInit, ProcessErrors, GetBasePath, HostsAdd, HostsReload, SelectionInit) {
    return function(params) {

        var inventory_id = params.inventory_id,
            group_id = params.group_id,
            list = HostList,
            generator = GenerateList,
            defaultUrl, scope;

        list.iterator = 'subhost';  //Override the iterator and name so the scope of the modal dialog
        list.name = 'subhosts';     //will not conflict with the parent scope



        scope = generator.inject(list, {
            id: 'form-modal-body',
            mode: 'select',
            breadCrumbs: false,
            selectButton: false
        });

        defaultUrl = GetBasePath('inventory') + inventory_id + '/hosts/?not__groups__id=' + scope.group_id;

        scope.formModalActionLabel = 'Select';
        scope.formModalHeader = 'Add Existing Hosts';
        scope.formModalCancelShow = true;

        SelectionInit({ scope: scope, list: list, url: GetBasePath('groups') + group_id + '/hosts/' });

        if (scope.removeModalClosed) {
            scope.removeModalClosed();
        }
        scope.removeModalClosed = scope.$on('modalClosed', function() {
            // if the modal closed, assume something got changed and reload the host list
            HostsReload(params);
        });

        $('.popover').popover('hide');  //remove any lingering pop-overs
        $('#form-modal .btn-none').removeClass('btn-none').addClass('btn-success');
        $('#form-modal').modal({ backdrop: 'static', keyboard: false });

        SearchInit({ scope: scope, set: 'subhosts', list: list, url: defaultUrl });
        PaginateInit({ scope: scope, list: list, url: defaultUrl, mode: 'lookup' });
        scope.search(list.iterator);

        if (!scope.$$phase) {
            scope.$digest();
        }

        scope.createHost = function() {
            $('#form-modal').modal('hide');
            HostsAdd({ scope: params.scope, inventory_id: inventory_id, group_id: group_id });
        };

    };
}])


.factory('HostsCreate', ['$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'HostForm', 'GenerateForm',
    'Prompt', 'ProcessErrors', 'GetBasePath', 'HostsReload', 'ParseTypeChange', 'Wait', 'ToJSON',
function($rootScope, $location, $log, $routeParams, Rest, Alert, HostForm, GenerateForm, Prompt, ProcessErrors,
    GetBasePath, HostsReload, ParseTypeChange, Wait, ToJSON) {
    return function(params) {

        var parent_scope = params.scope,
            inventory_id = parent_scope.inventory_id,
            group_id = parent_scope.selected_group_id,
            defaultUrl = GetBasePath('groups') + group_id + '/hosts/',
            form = HostForm,
            generator = GenerateForm,
            scope = generator.inject(form, {mode: 'add', modal: true, related: false}),
            master={};

        scope.formModalActionLabel = 'Save';
        scope.formModalHeader = 'Create New Host';
        scope.formModalCancelShow = true;

        scope.parseType = 'yaml';
        ParseTypeChange({ scope: scope, field_id: 'host_variables' });

        if (scope.removeHostsReload) {
            scope.removeHostsReload();
        }
        scope.removeHostsReload = scope.$on('hostsReload', function() {
            HostsReload(params);
        });

        $('#form-modal .btn-none').removeClass('btn-none').addClass('btn-success');
        //$('#form-modal').unbind('hidden');
        //$('#form-modal').on('hidden', function () { scope.$emit('hostsReload'); });

        generator.reset();
        master={};

        if (!scope.$$phase) {
            scope.$digest();
        }

        if (scope.removeHostSaveComplete) {
            scope.removeHostSaveComplete();
        }
        scope.removeHostSaveComplete = scope.$on('HostSaveComplete', function() {
            Wait('stop');
            $('#form-modal').modal('hide');

            HostsReload({
                scope: parent_scope,
                group_id: parent_scope.selected_group_id,
                tree_id: parent_scope.selected_tree_id,
                inventory_id: parent_scope.inventory_id
            });

            //WatchInventoryWindowResize();
        });

        // Save
        scope.formModalAction  = function() {

            Wait('start');

            var fld, data={};
            scope.formModalActionDisabled = true;
            data.variables = ToJSON(scope.parseType, scope.variables, true);
            for (fld in form.fields) {
                if (fld !== 'variables') {
                    data[fld] = scope[fld];
                }
            }
            data.inventory = inventory_id;

            Rest.setUrl(defaultUrl);
            Rest.post(data)
                .success( function() {
                    scope.$emit('HostSaveComplete');
                })
                .error( function(data, status) {
                    Wait('stop');
                    scope.formModalActionDisabled = false;
                    ProcessErrors(scope, data, status, form,
                        { hdr: 'Error!', msg: 'Failed to add new host. POST returned status: ' + status });
                });
        };

        // Cancel
        scope.formReset = function() {
            // Defaults
            generator.reset();
        };

        scope.cancelModal = function() {
            // WatchInventoryWindowResize();
        };

    };
}])


.factory('HostsEdit', ['$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'HostForm', 'GenerateForm',
    'Prompt', 'ProcessErrors', 'GetBasePath', 'HostsReload', 'ParseTypeChange', 'Wait', 'Find', 'SetStatus', 'ApplyEllipsis',
    'ToJSON', 'ParseVariableString', 'CreateDialog', 'TextareaResize',
function($rootScope, $location, $log, $routeParams, Rest, Alert, HostForm, GenerateForm, Prompt, ProcessErrors,
    GetBasePath, HostsReload, ParseTypeChange, Wait, Find, SetStatus, ApplyEllipsis, ToJSON,
    ParseVariableString, CreateDialog, TextareaResize) {
    return function(params) {

        var parent_scope = params.host_scope,
            group_scope = params.group_scope,
            host_id = params.host_id,
            inventory_id = params.inventory_id,
            mode = params.mode,  // 'add' or 'edit'
            selected_group_id = params.selected_group_id,
            generator = GenerateForm,
            form = HostForm,
            defaultUrl,
            scope = parent_scope.$new(),
            master = {},
            relatedSets = {},
            buttons, url;

        generator.inject(HostForm, { mode: 'edit', id: 'host-modal-dialog', breadCrumbs: false, related: false, scope: scope });
        generator.reset();

        buttons = [{
            label: "Cancel",
            onClick: function() {
                scope.cancelModal();
            },
            icon: "fa-times",
            "class": "btn btn-default",
            "id": "host-cancel-button"
        },{
            label: "Save",
            onClick: function() {
                scope.saveModal();
            },
            icon: "fa-check",
            "class": "btn btn-primary",
            "id": "host-save-button"
        }];

        CreateDialog({
            scope: scope,
            buttons: buttons,
            width: 675,
            height: 750,
            minWidth: 400,
            title: 'Host Properties',
            id: 'host-modal-dialog',
            clonseOnEscape: false,
            onClose: function() {
                Wait('stop');
                scope.codeMirror.destroy();
                $('#host-modal-dialog').empty();
            },
            onResizeStop: function() {
                TextareaResize({
                    scope: scope,
                    textareaId: 'host_variables',
                    modalId: 'host-modal-dialog',
                    formId: 'host_form'
                });
            },
            beforeDestroy: function() {
                if (scope.codeMirror) {
                    scope.codeMirror.destroy();
                }
                $('#host-modal-dialog').empty();
            },
            onOpen: function() {
                $('#host_name').focus();
            },
            callback: 'HostEditDialogReady'
        });

        scope.parseType = 'yaml';

        if (scope.hostVariablesLoadedRemove) {
            scope.hostVariablesLoadedRemove();
        }
        scope.hostVariablesLoadedRemove = scope.$on('hostVariablesLoaded', function() {
            $('#host-modal-dialog').dialog('open');
            setTimeout(function() {
                TextareaResize({
                    scope: scope,
                    textareaId: 'host_variables',
                    modalId: 'host-modal-dialog',
                    formId: 'host_form',
                    parse: true
                });
            }, 300);
            //ParseTypeChange({ scope: scope, field_id: 'host_variables', onReady: callback });
        });

        if (scope.hostLoadedRemove) {
            scope.hostLoadedRemove();
        }
        scope.hostLoadedRemove = scope.$on('hostLoaded', function() {
            // Retrieve host variables
            if (scope.variable_url) {
                Rest.setUrl(scope.variable_url);
                Rest.get()
                    .success( function(data) {
                        scope.variables = ParseVariableString(data);
                        scope.$emit('hostVariablesLoaded');
                    })
                    .error( function(data, status) {
                        scope.variables = null;
                        ProcessErrors(scope, data, status, form,
                            { hdr: 'Error!', msg: 'Failed to retrieve host variables. GET returned status: ' + status });
                    });
            }
            else {
                scope.variables = "---";
                scope.$emit('hostVariablesLoaded');
            }
            master.variables = scope.variables;
        });

        Wait('start');

        // Retrieve detail record and prepopulate the form
        if (mode === 'edit') {
            defaultUrl = GetBasePath('hosts') + host_id + '/';
            Rest.setUrl(defaultUrl);
            Rest.get()
                .success( function(data) {
                    var set, fld, related;
                    for (fld in form.fields) {
                        if (data[fld]) {
                            scope[fld] = data[fld];
                            master[fld] = scope[fld];
                        }
                    }
                    related = data.related;
                    for (set in form.related) {
                        if (related[set]) {
                            relatedSets[set] = { url: related[set], iterator: form.related[set].iterator };
                        }
                    }
                    scope.variable_url = data.related.variable_data;
                    scope.has_inventory_sources = data.has_inventory_sources;
                    scope.$emit('hostLoaded');
                })
                .error( function(data, status) {
                    ProcessErrors(parent_scope, data, status, form,
                        { hdr: 'Error!', msg: 'Failed to retrieve host: ' + host_id + '. GET returned status: ' + status });
                });
        }
        else {
            // Add mode
            url = GetBasePath('groups') + selected_group_id + '/';
            Rest.setUrl(url);
            Rest.get()
                .success( function(data) {
                    scope.has_inventory_sources = data.has_inventory_sources;
                    scope.enabled = true;
                    scope.variables = '---';
                    defaultUrl = data.related.hosts;
                    scope.$emit('hostVariablesLoaded');
                })
                .error( function(data, status) {
                    ProcessErrors(parent_scope, data, status, form,
                        { hdr: 'Error!', msg: 'Failed to retrieve group: ' + selected_group_id + '. GET returned status: ' + status });
                });
        }

        if (scope.removeSaveCompleted) {
            scope.removeSaveCompleted();
        }
        scope.removeSaveCompleted = scope.$on('saveCompleted', function() {
            try {
                $('#host-modal-dialog').dialog('close');
            }
            catch(err) {
                // ignore
            }
            if (group_scope && group_scope.refreshHosts) {
                group_scope.refreshHosts();
            }
            if (parent_scope.refreshHosts) {
                parent_scope.refreshHosts();
            }
            scope.$destroy();
        });

        // Save changes to the parent
        scope.saveModal = function() {

            Wait('start');
            var fld, data={};

            try {
                data.variables = ToJSON(scope.parseType, scope.variables, true);
                for (fld in form.fields) {
                    data[fld] = scope[fld];
                }
                data.inventory = inventory_id;
                Rest.setUrl(defaultUrl);
                if (mode === 'edit') {
                    Rest.put(data)
                        .success( function() {
                            scope.$emit('saveCompleted');
                        })
                        .error( function(data, status) {
                            ProcessErrors(scope, data, status, form,
                                { hdr: 'Error!', msg: 'Failed to update host: ' + host_id + '. PUT returned status: ' + status });
                        });
                }
                else {
                    Rest.post(data)
                        .success( function() {
                            scope.$emit('saveCompleted');
                        })
                        .error( function(data, status) {
                            ProcessErrors(scope, data, status, form,
                                { hdr: 'Error!', msg: 'Failed to create host. POST returned status: ' + status });
                        });
                }
            }
            catch(e) {
                // ignore. ToJSON will have already alerted the user
            }
        };

        // Cancel
        scope.formReset = function() {
            generator.reset();
            for (var fld in master) {
                scope[fld] = master[fld];
            }
            scope.parseType = 'yaml';
        };

        scope.cancelModal = function() {
            try {
                $('#host-modal-dialog').dialog('close');
            }
            catch(err) {
                // ignore
            }
            scope.$destroy();
        };

    };
}])


.factory('HostsDelete', ['$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'Prompt', 'ProcessErrors', 'GetBasePath', 'HostsReload', 'Wait',
function($rootScope, $location, $log, $routeParams, Rest, Alert, Prompt, ProcessErrors, GetBasePath, HostsReload, Wait) {
    return function(params) {
        // Remove the selected host from the current group by disassociating

        var action_to_take, body,
            scope = params.parent_scope,
            host_id = params.host_id,
            host_name = params.host_name,
            group,
            url_list = [];

        if (scope.selected_group_id) {
            //group = Find({ list: parent_scope.groups, key: 'id', val: parent_scope.selected_group_id });
            //getChildren(group.id);
            url_list.push(GetBasePath('groups') + scope.selected_group_id + '/hosts/');
        }
        else {
            url_list.push(GetBasePath('inventory') + scope.inventory.id + '/hosts/');
        }

        if (scope.removeHostsReload) {
            scope.removeHostsReload();
        }
        scope.removeHostsReload = scope.$on('hostsReload', function() {
            $('#prompt-modal').modal('hide');
            scope.refreshHosts();
        });

        $('#prompt-modal').on('hidden.bs.modal', function(){ Wait('stop'); });

        action_to_take = function() {
            var count=0, i;

            Wait('start');

            if (scope.removeHostRemoved) {
                scope.removeHostRemoved();
            }
            scope.removeHostRemoved = scope.$on('hostRemoved', function(){
                count++;
                if (count === url_list.length) {
                    Wait('start');
                    scope.$emit('hostsReload');
                }
            });

            for(i=0; i < url_list.length; i++) {
                Rest.setUrl(url_list[i]);
                Rest.post({ id: host_id, disassociate: 1 })
                    .success( function() {
                        scope.$emit('hostRemoved');
                    })
                    .error( function(data, status) {
                        ProcessErrors(scope, data, status, null,
                            { hdr: 'Error!', msg: 'Attempt to delete ' + host_name + ' failed. DELETE returned status: ' + status });
                    });
            }
        };

        body = (group) ? '<div class=\"alert alert-info\"><p>Are you sure you want to remove host <strong>' + host_name + '</strong> from group ' + group.name + '?' +
            ' It will still be part of the inventory and available in All Hosts.</p></div>' :
            '<div class=\"alert alert-info\"><p>Are you sure you want to permanently delete host <strong>' + host_name + '</strong> from the inventory?</p></div>';
        Prompt({ hdr: 'Delete Host', body: body, action: action_to_take, 'class': 'btn-danger' });

    };
}])

.factory('HostsCopy', ['$compile', 'Rest', 'ProcessErrors', 'CreateDialog', 'GetBasePath', 'Wait', 'GenerateList', 'GroupList', 'SearchInit',
    'PaginateInit',
    function($compile, Rest, ProcessErrors, CreateDialog, GetBasePath, Wait, GenerateList, GroupList, SearchInit, PaginateInit) {
    return function(params) {

        var host_id = params.host_id,
            group_scope = params.group_scope,
            parent_scope = params.host_scope,
            parent_group = group_scope.selected_group_id,
            scope = parent_scope.$new(),
            buttonSet, url, host;

        buttonSet = [{
            label: "Cancel",
            onClick: function() {
                scope.cancel();
            },
            icon: "fa-times",
            "class": "btn btn-default",
            "id": "host-copy-cancel-button"
        },{
            label: "OK",
            onClick: function() {
                scope.performCopy();
            },
            icon: "fa-check",
            "class": "btn btn-primary",
            "id": "host-copy-ok-button"
        }];

        if (scope.removeHostCopyPostRefresh) {
            scope.removeHostCopyPostRefresh();
        }
        scope.removeHostCopyPostRefresh = scope.$on('PostRefresh', function() {
            scope.copy_groups.forEach(function(row, i) {
                scope.copy_groups[i].checked = '0';
            });
            Wait('stop');
            $('#host-copy-dialog').dialog('open');
            $('#host-copy-ok-button').attr('disabled','disabled');

            // prevent backspace from navigation when not in input or textarea field
            $(document).on("keydown", function (e) {
                if (e.which === 8 && !$(e.target).is('input[type="text"], textarea')) {
                    e.preventDefault();
                }
            });
        });

        if (scope.removeHostCopyDialogReady) {
            scope.removeHostCopyDialogReady();
        }
        scope.removeCopyDialogReady = scope.$on('HostCopyDialogReady', function() {
            var url = GetBasePath('inventory') + group_scope.inventory.id + '/groups/';
            GenerateList.inject(GroupList, {
                mode: 'lookup',
                id: 'copy-host-select-container',
                scope: scope
                //,
                //instructions: instructions
            });
            SearchInit({
                scope: scope,
                set: GroupList.name,
                list: GroupList,
                url: url
            });
            PaginateInit({
                scope: scope,
                list: GroupList,
                url: url,
                mode: 'lookup'
            });
            scope.search(GroupList.iterator, null, true, false);
        });

        if (scope.removeShowDialog) {
            scope.removeShowDialog();
        }
        scope.removeShowDialog = scope.$on('ShowDialog', function() {
            var d;
            scope.name = host.name;
            scope.copy_choice = "copy";
            d = angular.element(document.getElementById('host-copy-dialog'));
            $compile(d)(scope);
            CreateDialog({
                id: 'host-copy-dialog',
                scope: scope,
                buttons: buttonSet,
                width: 650,
                height: 650,
                minWidth: 600,
                title: 'Copy or Move Host',
                callback: 'HostCopyDialogReady',
                onClose: function() {
                    scope.cancel();
                }
            });
        });

        Wait('start');

        url = GetBasePath('hosts') + host_id + '/';
        Rest.setUrl(url);
        Rest.get()
            .success(function(data) {
                host = data;
                scope.$emit('ShowDialog');
            })
            .error(function(data, status) {
                ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                    msg: 'Call to ' + url + ' failed. GET returned: ' + status });
            });


        scope.cancel = function() {
            $(document).off("keydown");
            try {
                $('#host-copy-dialog').dialog('close');
            }
            catch(e) {
                // ignore
            }
            scope.searchCleanup();
            group_scope.restoreSearch();  // Restore all parent search stuff and refresh hosts and groups lists
            scope.$destroy();
        };

        scope['toggle_' + GroupList.iterator] = function (id) {
            var count = 0,
                list = GroupList;
            scope[list.name].forEach( function(row, i) {
                if (row.id === id) {
                    if (row.checked === '0') {
                        scope[list.name][i].checked = '1';
                        scope[list.name][i].success_class = 'success';
                    }
                    else {
                        scope[list.name][i].checked = '0';
                        scope[list.name][i].success_class = '';
                    }
                } else {
                    scope[list.name][i].checked = '0';
                    scope[list.name][i].success_class = '';
                }
            });
            // Check if any rows are checked
            scope[list.name].forEach(function(row) {
                if (row.checked === '1') {
                    count++;
                }
            });
            if (count === 0) {
                $('#host-copy-ok-button').attr('disabled','disabled');
            }
            else {
                $('#host-copy-ok-button').removeAttr('disabled');
            }
        };

        scope.performCopy = function() {
            var list = GroupList,
                target,
                url;

            Wait('start');

            if (scope.use_root_group) {
                target = null;
            }
            else {
                scope[list.name].every(function(row) {
                    if (row.checked === '1') {
                        target = row;
                        return false;
                    }
                    return true;
                });
            }

            if (scope.copy_choice === 'move') {
                // Respond to move

                // disassociate the host from the original parent
                if (scope.removeHostRemove) {
                    scope.removeHostRemove();
                }
                scope.removeHostRemove = scope.$on('RemoveHost', function () {
                    if (parent_group > 0) {
                        // Only remove a host from a parent when the parent is a group and not the inventory root
                        url = GetBasePath('groups') + parent_group + '/hosts/';
                        Rest.setUrl(url);
                        Rest.post({ id: host.id, disassociate: 1 })
                            .success(function () {
                                scope.cancel();
                            })
                            .error(function (data, status) {
                                ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                                    msg: 'Failed to remove ' + host.name + ' from group ' + parent_group + '. POST returned: ' + status });
                            });
                    } else {
                        scope.cancel();
                    }
                });

                // add the new host to the target
                url = GetBasePath('groups') + target.id + '/hosts/';
                Rest.setUrl(url);
                Rest.post(host)
                    .success(function () {
                        scope.$emit('RemoveHost');
                    })
                    .error(function (data, status) {
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                            msg: 'Failed to add ' + host.name + ' to ' + target.name + '. POST returned: ' + status });
                    });
            }
            else {
                // Respond to copy by adding the new host to the target
                url = GetBasePath('groups') + target.id + '/hosts/';
                Rest.setUrl(url);
                Rest.post(host)
                    .success(function () {
                        scope.cancel();
                    })
                    .error(function (data, status) {
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                            msg: 'Failed to add ' + host.name + ' to ' + target.name + '. POST returned: ' + status
                        });
                    });
            }
        };


    };
}])

.factory('EditHostGroups', ['$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'GenerateForm', 'Prompt',
    'ProcessErrors', 'GetBasePath', 'HostsReload', 'ParseTypeChange', 'Wait',
function($rootScope, $location, $log, $routeParams, Rest, Alert, GenerateForm, Prompt, ProcessErrors, GetBasePath, HostsReload,
    ParseTypeChange, Wait) {
    return function(params) {

        var host_id = params.host_id,
            inventory_id = params.inventory_id,
            generator = GenerateForm,
            actions = [],
            i, html, defaultUrl, scope, postAction;

        html = "<div class=\"row host-groups\">\n";
        html += "<div class=\"col-lg-6\">\n";
        html += "<label>Available Groups:</label>\n";
        html += "<select multiple class=\"form-control\" name=\"available-groups\" ng-model=\"selectedGroups\" ng-change=\"leftChange()\" " +
            "ng-options=\"avail_group.name for avail_group in available_groups\"></select>\n";
        html += "</div>\n";
        html += "<div class=\"col-lg-6\">\n";
        html += "<label>Belongs to Groups:</label>\n";
        html += "<select multiple class=\"form-control\" name=\"selected-groups\" ng-model=\"assignedGroups\" ng-change=\"rightChange()\" " +
            "ng-options=\"host_group.name for host_group in host_groups\"></select>\n";
        html += "</div>\n";
        html += "</div>\n";
        html += "<div class=\"row host-group-buttons\">\n";
        html += "<div class=\"col-lg-12\">\n";
        html += "<button type=\"button\" ng-click=\"moveLeft()\" class=\"btn btn-sm btn-primary left-button\" ng-disabled=\"leftButtonDisabled\">" +
            "<i class=\"icon-arrow-left\"></i></button>\n";
        html += "<button type=\"button\" ng-click=\"moveRight()\" class=\"btn btn-sm btn-primary right-button\" ng-disabled=\"rightButtonDisabled\">" +
            "<i class=\"icon-arrow-right\"></i></button>\n";
        html += "<p>(move selected groups)</p>\n";
        html += "</div>\n";
        html += "</div>\n";

        defaultUrl =  GetBasePath('hosts') + host_id + '/';
        scope = generator.inject(null, { mode: 'edit', modal: true, related: false, html: html });

        for (i=0; i < scope.hosts.length; i++) {
            if (scope.hosts[i].id === host_id) {
                scope.host = scope.hosts[i];
            }
        }

        scope.selectedGroups = null;
        scope.assignedGroups = null;
        scope.leftButtonDisabled = true;
        scope.rightButtonDisabled = true;

        scope.formModalActionLabel = 'Save';
        //scope.formModalHeader = 'Host Groups';
        scope.formModalHeader = scope.host.name + ' - <span class=\"subtitle\">Groups</span>';
        scope.formModalCancelShow = true;
        scope.formModalActionDisabled = true;

        $('#form-modal .btn-none').removeClass('btn-none').addClass('btn-success');

        if (scope.hostGroupChangeRemove) {
            scope.hostGroupChangeRemove();
        }
        scope.hostGroupChangeRemove = scope.$on('hostGroupChange', function() {
            actions.pop();
            if (actions.length === 0) {
                postAction = function() {
                    setTimeout(function() { Wait('stop'); }, 500);
                };
                HostsReload({ scope: scope, inventory_id: inventory_id, group_id: scope.group_id , action: postAction });
            }
        });

        // Save changes
        scope.formModalAction = function() {
            var i, j, found;

            $('#form-modal').modal('hide');
            Wait('start');

            // removed host from deleted groups
            for (i=0; i < scope.original_groups.length; i++) {
                found = false;
                for (j=0; j < scope.host_groups.length; j++) {
                    if (scope.original_groups[i].id === scope.host_groups[j].id) {
                        found = true;
                    }
                }
                if (!found) {
                    // group was removed
                    actions.push({ group_id: scope.original_groups[i].id , action: 'delete' });
                    Rest.setUrl(GetBasePath('groups') + scope.original_groups[i].id + '/hosts/');
                    Rest.post({ id: host_id, disassociate: 1 })
                        .success( function() {
                            scope.$emit('hostGroupChange');
                        })
                        .error( function(data, status) {
                            scope.$emit('hostGroupChange');
                            ProcessErrors(scope, data, status, null,
                               { hdr: 'Error!', msg: 'Attempt to remove host from group ' + scope.original_groups[i].name +
                               ' failed. POST returned status: ' + status });
                        });
                }
            }

            // add host to new groups
            for (i=0; i < scope.host_groups.length; i++) {
                found = false;
                for (j=0; j < scope.original_groups.length; j++) {
                    if (scope.original_groups[j].id === scope.host_groups[i].id) {
                        found = true;
                    }
                }
                if (!found) {
                    // group was added
                    actions.push({ group_id: scope.host_groups[i].id , action: 'add' });
                    Rest.setUrl(GetBasePath('groups') + scope.host_groups[i].id + '/hosts/');
                    Rest.post(scope.host)
                        .success( function() {
                            scope.$emit('hostGroupChange');
                        })
                        .error( function(data, status) {
                            scope.$emit('hostGroupChange');
                            ProcessErrors(scope, data, status, null,
                                { hdr: 'Error!', msg: 'Attempt to add host to group ' + scope.host_groups[i].name +
                                ' failed. POST returned status: ' + status });
                        });
                }
            }
        };

        scope.leftChange = function() {
            // Select/deselect on available groups list
            if (scope.selectedGroups !== null && scope.selectedGroups.length > 0) {
                scope.assignedGroups = null;
                scope.leftButtonDisabled = true;
                scope.rightButtonDisabled = false;
            }
            else {
                scope.rightButtonDisabled = true;
            }
        };

        scope.rightChange = function() {
            // Select/deselect made on host groups list
            if (scope.assignedGroups !== null && scope.assignedGroups.length > 0) {
                scope.selectedGroups = null;
                scope.leftButtonDisabled = false;
                scope.rightButtonDisabled = true;
            }
            else {
                scope.leftButtonDisabled = true;
            }
        };

        scope.moveLeft = function() {
            // Remove selected groups from the list of assigned groups

            var i, j, found, placed;

            for (i=0; i < scope.assignedGroups.length; i++){
                for (j=0 ; j < scope.host_groups.length; j++) {
                    if (scope.host_groups[j].id === scope.assignedGroups[i].id) {
                        scope.host_groups.splice(j,1);
                        break;
                    }
                }
            }
            for (i=0; i < scope.assignedGroups.length; i++){
                found = false;
                for (j=0; j < scope.available_groups.length && !found; j++){
                    if (scope.available_groups[j].id === scope.assignedGroups[i].id) {
                        found=true;
                    }
                }
                if (!found) {
                    placed = false;
                    for (j=0; j < scope.available_groups.length && !placed; j++){
                        if (j === 0 && scope.assignedGroups[i].name.toLowerCase() < scope.available_groups[j].name.toLowerCase()) {
                            // prepend to the beginning of the array
                            placed=true;
                            scope.available_groups.unshift(scope.assignedGroups[i]);
                        }
                        else if (j + 1 < scope.available_groups.length) {
                            if (scope.assignedGroups[i].name.toLowerCase() > scope.available_groups[j].name.toLowerCase() &&
                                scope.assignedGroups[i].name.toLowerCase() < scope.available_groups[j + 1].name.toLowerCase() ) {
                                // insert into the middle of the array
                                placed = true;
                                scope.available_groups.splice(j + 1, 0, scope.assignedGroups[i]);
                            }
                        }
                    }
                    if (!placed) {
                        // append to the end of the array
                        scope.available_groups.push(scope.assignedGroups[i]);
                    }
                }
            }
            scope.assignedGroups = null;
            scope.leftButtonDisabled = true;
            scope.rightButtonDisabled = true;
            scope.formModalActionDisabled = false;
        };

        scope.moveRight = function() {
             // Remove selected groups from list of available groups

            var i, j, found, placed;

            for (i=0; i < scope.selectedGroups.length; i++){
                for (j=0 ; j < scope.available_groups.length; j++) {
                    if (scope.available_groups[j].id === scope.selectedGroups[i].id) {
                        scope.available_groups.splice(j,1);
                        break;
                    }
                }
            }
            for (i=0; i < scope.selectedGroups.length; i++){
                found = false;
                for (j=0; j < scope.host_groups.length && !found; j++){
                    if (scope.host_groups[j].id === scope.selectedGroups[i].id) {
                        found=true;
                    }
                }
                if (!found) {
                    placed = false;
                    for (j=0; j < scope.host_groups.length && !placed; j++) {
                        if (j === 0 && scope.selectedGroups[i].name.toLowerCase() < scope.host_groups[j].name.toLowerCase()) {
                            // prepend to the beginning of the array
                            placed=true;
                            scope.host_groups.unshift(scope.selectedGroups[i]);
                        }
                        else if (j + 1 < scope.host_groups.length) {
                            if (scope.selectedGroups[i].name.toLowerCase() > scope.host_groups[j].name.toLowerCase() &&
                                scope.selectedGroups[i].name.toLowerCase() < scope.host_groups[j + 1].name.toLowerCase() ) {
                                // insert into the middle of the array
                                placed = true;
                                scope.host_groups.splice(j + 1, 0, scope.selectedGroups[i]);
                            }
                        }
                    }
                    if (!placed) {
                        // append to the end of the array
                        scope.host_groups.push(scope.selectedGroups[i]);
                    }
                }
            }
            scope.selectedGroups = null;
            scope.leftButtonDisabled = true;
            scope.rightButtonDisabled = true;
            scope.formModalActionDisabled = false;
        };


        // Load the host's current list of groups
        scope.host_groups = [];
        scope.original_groups = [];
        scope.available_groups = [];
        Rest.setUrl(scope.host.related.groups + '?order_by=name');
        Rest.get()
            .success( function(data) {
                var i, j, found;
                for (i=0; i < data.results.length; i++) {
                    scope.host_groups.push({
                        id: data.results[i].id,
                        name: data.results[i].name,
                        description: data.results[i].description
                    });
                    scope.original_groups.push({
                        id: data.results[i].id,
                        name: data.results[i].name,
                        description: data.results[i].description
                    });
                }
                for (i=0; i < scope.inventory_groups.length; i++) {
                    found =  false;
                    for (j=0; j < scope.host_groups.length; j++) {
                        if (scope.inventory_groups[i].id === scope.host_groups[j].id) {
                            found = true;
                        }
                    }
                    if (!found) {
                        scope.available_groups.push(scope.inventory_groups[i]);
                    }
                }
            })
            .error( function(data, status) {
                ProcessErrors(scope, data, status, null,
                    { hdr: 'Error!', msg: 'Failed to get current groups for host: ' + host_id + '. GET returned: ' + status });
            });

        if (scope.removeHostsReload) {
            scope.removeHostsReload();
        }
        scope.removeHostsReload = scope.$on('hostsReload', function() {
            HostsReload(params);
        });

        if (!scope.$$phase) {
            scope.$digest();
        }
    };
}]);






