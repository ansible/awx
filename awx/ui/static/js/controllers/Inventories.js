/************************************
 * Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *
 *  Inventories.js
 *
 *  Controller functions for the Inventory model.
 *
 */
/**
 * @ngdoc function
 * @name controllers.function:Inventories
 * @description This controller's for the Inventory page
*/


export function InventoriesList($scope, $rootScope, $location, $log, $routeParams, $compile, $filter, Rest, Alert, InventoryList, GenerateList,
    LoadBreadCrumbs, Prompt, SearchInit, PaginateInit, ReturnToCaller, ClearScope, ProcessErrors, GetBasePath, Wait, Stream,
    EditInventoryProperties, Find, Empty, LogViewer) {

    //ClearScope();

    var list = InventoryList,
        defaultUrl = GetBasePath('inventory'),
        view = GenerateList,
        paths = $location.path().replace(/^\//, '').split('/'),
        mode = (paths[0] === 'inventories') ? 'edit' : 'select';

    function ellipsis(a) {
        if (a.length > 20) {
            return a.substr(0,20) + '...';
        }
        return a;
    }

    function attachElem(event, html, title) {
        var elem = $(event.target).parent();
        try {
            elem.tooltip('hide');
            elem.popover('destroy');
        }
        catch(err) {
            //ignore
        }
        $('.popover').each(function() {
            // remove lingering popover <div>. Seems to be a bug in TB3 RC1
            $(this).remove();
        });
        $('.tooltip').each( function() {
            // close any lingering tool tipss
            $(this).hide();
        });
        elem.attr({ "aw-pop-over": html, "data-popover-title": title, "data-placement": "right" });
        $compile(elem)($scope);
        elem.on('shown.bs.popover', function() {
            $('.popover').each(function() {
                $compile($(this))($scope);  //make nested directives work!
            });
            $('.popover-content, .popover-title').click(function() {
                elem.popover('hide');
            });
        });
        elem.popover('show');
    }

    view.inject(InventoryList, { mode: mode, scope: $scope });
    $rootScope.flashMessage = null;

    SearchInit({
        scope: $scope,
        set: 'inventories',
        list: list,
        url: defaultUrl
    });

    PaginateInit({
        scope: $scope,
        list: list,
        url: defaultUrl
    });

    if ($routeParams.name) {
        $scope[InventoryList.iterator + 'InputDisable'] = false;
        $scope[InventoryList.iterator + 'SearchValue'] = $routeParams.name;
        $scope[InventoryList.iterator + 'SearchField'] = 'name';
        $scope[InventoryList.iterator + 'SearchFieldLabel'] = InventoryList.fields.name.label;
        $scope[InventoryList.iterator + 'SearchSelectValue'] = null;
    }

    if ($routeParams.has_active_failures) {
        $scope[InventoryList.iterator + 'InputDisable'] = true;
        $scope[InventoryList.iterator + 'SearchValue'] = $routeParams.has_active_failures;
        $scope[InventoryList.iterator + 'SearchField'] = 'has_active_failures';
        $scope[InventoryList.iterator + 'SearchFieldLabel'] = InventoryList.fields.has_active_failures.label;
        $scope[InventoryList.iterator + 'SearchSelectValue'] = ($routeParams.has_active_failures === 'true') ? {
            value: 1
        } : {
            value: 0
        };
    }

    if ($routeParams.has_inventory_sources) {
        $scope[InventoryList.iterator + 'InputDisable'] = true;
        $scope[InventoryList.iterator + 'SearchValue'] = $routeParams.has_inventory_sources;
        $scope[InventoryList.iterator + 'SearchField'] = 'has_inventory_sources';
        $scope[InventoryList.iterator + 'SearchFieldLabel'] = InventoryList.fields.has_inventory_sources.label;
        $scope[InventoryList.iterator + 'SearchSelectValue'] = ($routeParams.has_inventory_sources === 'true') ? {
            value: 1
        } : {
            value: 0
        };
    }

    if ($routeParams.inventory_sources_with_failures) {
        // pass a value of true, however this field actually contains an integer value
        $scope[InventoryList.iterator + 'InputDisable'] = true;
        $scope[InventoryList.iterator + 'SearchValue'] = $routeParams.inventory_sources_with_failures;
        $scope[InventoryList.iterator + 'SearchField'] = 'inventory_sources_with_failures';
        $scope[InventoryList.iterator + 'SearchFieldLabel'] = InventoryList.fields.inventory_sources_with_failures.label;
        $scope[InventoryList.iterator + 'SearchType'] = 'gtzero';
    }

    $scope.search(list.iterator);

    LoadBreadCrumbs();

    if ($scope.removePostRefresh) {
        $scope.removePostRefresh();
    }
    $scope.removePostRefresh = $scope.$on('PostRefresh', function () {
        //If we got here by deleting an inventory, stop the spinner and cleanup events
        Wait('stop');
        try {
            $('#prompt-modal').modal('hide');
        }
        catch(e) {
            // ignore
        }
        $scope.inventories.forEach(function(inventory, idx) {
            $scope.inventories[idx].launch_class = "";
            if (inventory.has_inventory_sources) {
                if (inventory.inventory_sources_with_failures > 0) {
                    $scope.inventories[idx].syncStatus = 'error';
                    $scope.inventories[idx].syncTip = inventory.inventory_sources_with_failures + ' groups with sync failures. Click for details';
                }
                else {
                    $scope.inventories[idx].syncStatus = 'successful';
                    $scope.inventories[idx].syncTip = 'No inventory sync failures. Click for details.';
                }
            }
            else {
                $scope.inventories[idx].syncStatus = 'na';
                $scope.inventories[idx].syncTip = 'Not configured for inventory sync.';
                $scope.inventories[idx].launch_class = "btn-disabled";
            }
            if (inventory.has_active_failures) {
                $scope.inventories[idx].hostsStatus = 'error';
                $scope.inventories[idx].hostsTip = inventory.hosts_with_active_failures + ' hosts with failures. Click for details.';
            }
            else if (inventory.total_hosts) {
                $scope.inventories[idx].hostsStatus = 'successful';
                $scope.inventories[idx].hostsTip = 'No hosts with failures. Click for details.';
            }
            else {
                $scope.inventories[idx].hostsStatus = 'none';
                $scope.inventories[idx].hostsTip = 'Inventory contains 0 hosts.';
            }
        });
    });

    if ($scope.removeRefreshInventories) {
        $scope.removeRefreshInventories();
    }
    $scope.removeRefreshInventories = $scope.$on('RefreshInventories', function () {
        // Reflect changes after inventory properties edit completes
        $scope.search(list.iterator);
    });

    if ($scope.removeHostSummaryReady) {
        $scope.removeHostSummaryReady();
    }
    $scope.removeHostSummaryReady = $scope.$on('HostSummaryReady', function(e, event, data) {

        var html, title = "Recent Jobs";
        Wait('stop');
        if (data.count > 0) {
            html = "<table class=\"table table-condensed flyout\" style=\"width: 100%\">\n";
            html += "<thead>\n";
            html += "<tr>";
            html += "<th>Status</th>";
            html += "<th>Finished</th>";
            html += "<th>Name</th>";
            html += "</tr>\n";
            html += "</thead>\n";
            html += "<tbody>\n";

            data.results.forEach(function(row) {
                html += "<tr>\n";
                html += "<td><a href=\"#/jobs/" + row.id + "\" " + "aw-tool-tip=\"" + row.status.charAt(0).toUpperCase() + row.status.slice(1) +
                    ". Click for details\" aw-tip-placement=\"top\"><i class=\"fa icon-job-" + row.status + "\"></i></a></td>\n";
                html += "<td>" + ($filter('date')(row.finished,'MM/dd HH:mm:ss')).replace(/ /,'<br />') + "</td>";
                html += "<td><a href=\"#/jobs/" + row.id + "\" " + "aw-tool-tip=\"" + row.status.charAt(0).toUpperCase() + row.status.slice(1) +
                    ". Click for details\" aw-tip-placement=\"top\">" + ellipsis(row.name) + "</a></td>";
                html += "</tr>\n";
            });
            html += "</tbody>\n";
            html += "</table>\n";
        }
        else {
            html = "<p>No recent job data available for this inventory.</p>\n";
        }
        attachElem(event, html, title);
    });

    if ($scope.removeGroupSummaryReady) {
        $scope.removeGroupSummaryReady();
    }
    $scope.removeGroupSummaryReady = $scope.$on('GroupSummaryReady', function(e, event, inventory, data) {
        var html, title;

        Wait('stop');

        // Build the html for our popover
        html = "<table class=\"table table-condensed flyout\" style=\"width: 100%\">\n";
        html += "<thead>\n";
        html += "<tr>";
        html += "<th>Status</th>";
        html += "<th>Last Sync</th>";
        html += "<th>Group</th>";
        html += "</tr>";
        html += "</thead>\n";
        html += "<tbody>\n";
        data.results.forEach( function(row) {
            if (row.related.last_update) {
                html += "<tr>";
                html += "<td><a href=\"\" ng-click=\"viewJob('" + row.related.last_update + "')\" aw-tool-tip=\"" + row.status.charAt(0).toUpperCase() + row.status.slice(1) + ". Click for details\" aw-tip-placement=\"top\"><i class=\"fa icon-job-" + row.status + "\"></i></a></td>";
                html += "<td>" + ($filter('date')(row.last_updated,'MM/dd HH:mm:ss')).replace(/ /,'<br />') + "</td>";
                html += "<td><a href=\"\" ng-click=\"viewJob('" + row.related.last_update + "')\">" + ellipsis(row.summary_fields.group.name) + "</a></td>";
                html += "</tr>\n";
            }
            else {
                html += "<tr>";
                html += "<td><a href=\"\" aw-tool-tip=\"No sync data\" aw-tip-placement=\"top\"><i class=\"fa icon-job-none\"></i></a></td>";
                html += "<td>NA</td>";
                html += "<td><a href=\"\">" + ellipsis(row.summary_fields.group.name) + "</a></td>";
                html += "</tr>\n";
            }
        });
        html += "</tbody>\n";
        html += "</table>\n";
        title = "Sync Status";
        attachElem(event, html, title);
    });

    $scope.showGroupSummary = function(event, id) {
        var inventory;
        if (!Empty(id)) {
            inventory = Find({ list: $scope.inventories, key: 'id', val: id });
            if (inventory.syncStatus !== 'na') {
                Wait('start');
                Rest.setUrl(inventory.related.inventory_sources + '?or__source=ec2&or__source=rax&order_by=-last_job_run&page_size=5');
                Rest.get()
                    .success(function(data) {
                        $scope.$emit('GroupSummaryReady', event, inventory, data);
                    })
                    .error(function(data, status) {
                        ProcessErrors( $scope, data, status, null, { hdr: 'Error!',
                            msg: 'Call to ' + inventory.related.inventory_sources + ' failed. GET returned status: ' + status
                        });
                    });
            }
        }
    };

    $scope.showHostSummary = function(event, id) {
        var url, inventory;
        if (!Empty(id)) {
            inventory = Find({ list: $scope.inventories, key: 'id', val: id });
            if (inventory.total_hosts > 0) {
                Wait('start');
                url = GetBasePath('jobs') + "?type=job&inventory=" + id + "&failed=";
                url += (inventory.has_active_failures) ? 'true' : "false";
                url += "&order_by=-finished&page_size=5";
                Rest.setUrl(url);
                Rest.get()
                    .success( function(data) {
                        $scope.$emit('HostSummaryReady', event, data);
                    })
                    .error( function(data, status) {
                        ProcessErrors( $scope, data, status, null, { hdr: 'Error!',
                            msg: 'Call to ' + url + ' failed. GET returned: ' + status
                        });
                    });
            }
        }
    };

    $scope.viewJob = function(url) {
        LogViewer({
            scope: $scope,
            url: url
        });
    };

    $scope.showActivity = function () {
        Stream({ scope:  $scope });
    };

    $scope.editInventoryProperties = function (inventory_id) {
        EditInventoryProperties({ scope: $scope, inventory_id: inventory_id });
    };

    $scope.addInventory = function () {
        $location.path($location.path() + '/add');
    };

    $scope.editInventory = function (id) {
        $location.path($location.path() + '/' + id);
    };

    $scope.deleteInventory = function (id, name) {

        var action = function () {
            var url = defaultUrl + id + '/';
            Wait('start');
            $('#prompt-modal').modal('hide');
            Rest.setUrl(url);
            Rest.destroy()
                .success(function () {
                    $scope.search(list.iterator);
                })
                .error(function (data, status) {
                    ProcessErrors( $scope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + ' failed. DELETE returned status: ' + status
                    });
                });
        };

        Prompt({
            hdr: 'Delete',
            body: '<div class=\"alert alert-info\">Delete inventory ' + name + '?</div>',
            action: action
        });
    };

    $scope.lookupOrganization = function (organization_id) {
        Rest.setUrl(GetBasePath('organizations') + organization_id + '/');
        Rest.get()
            .success(function (data) {
                return data.name;
            });
    };


    // Failed jobs link. Go to the jobs tabs, find all jobs for the inventory and sort by status
    $scope.viewJobs = function (id) {
        $location.url('/jobs/?inventory__int=' + id);
    };

    $scope.viewFailedJobs = function (id) {
        $location.url('/jobs/?inventory__int=' + id + '&status=failed');
    };
}

InventoriesList.$inject = ['$scope', '$rootScope', '$location', '$log', '$routeParams', '$compile', '$filter', 'Rest', 'Alert', 'InventoryList', 'GenerateList',
    'LoadBreadCrumbs', 'Prompt', 'SearchInit', 'PaginateInit', 'ReturnToCaller', 'ClearScope', 'ProcessErrors',
    'GetBasePath', 'Wait', 'Stream', 'EditInventoryProperties', 'Find', 'Empty', 'LogViewer'
];


export function InventoriesAdd($scope, $rootScope, $compile, $location, $log, $routeParams, InventoryForm, GenerateForm, Rest,
    Alert, ProcessErrors, LoadBreadCrumbs, ReturnToCaller, ClearScope, GenerateList, OrganizationList, SearchInit, PaginateInit,
    LookUpInit, GetBasePath, ParseTypeChange, Wait, ToJSON) {

    ClearScope();

    // Inject dynamic view
    var defaultUrl = GetBasePath('inventory'),
        form = InventoryForm,
        generator = GenerateForm;

    form.well = true;
    form.formLabelSize = null;
    form.formFieldSize = null;

    generator.inject(form, { mode: 'add', related: false, scope: $scope });

    generator.reset();
    LoadBreadCrumbs();

    $scope.parseType = 'yaml';
    ParseTypeChange({
        scope: $scope,
        variable: 'variables',
        parse_variable: 'parseType',
        field_id: 'inventory_variables'
    });

    LookUpInit({
        scope:  $scope,
        form: form,
        current_item: ($routeParams.organization_id) ? $routeParams.organization_id : null,
        list: OrganizationList,
        field: 'organization',
        input_type: 'radio'
    });

    // Save
    $scope.formSave = function () {
        generator.clearApiErrors();
        Wait('start');
        try {
            var fld, json_data, data;

            json_data = ToJSON($scope.parseType, $scope.variables, true);

            data = {};
            for (fld in form.fields) {
                if (fld !== 'variables') {
                    if (form.fields[fld].realName) {
                        data[form.fields[fld].realName] =  $scope[fld];
                    } else {
                        data[fld] =  $scope[fld];
                    }
                }
            }

            if ($scope.removeUpdateInventoryVariables) {
                $scope.removeUpdateInventoryVariables();
            }
            $scope.removeUpdateInventoryVariables = $scope.$on('UpdateInventoryVariables', function(e, data) {
                var inventory_id = data.id;
                Rest.setUrl(data.related.variable_data);
                Rest.put(json_data)
                    .success(function () {
                        Wait('stop');
                        $location.path('/inventories/' + inventory_id + '/');
                    })
                    .error(function (data, status) {
                        ProcessErrors( $scope, data, status, null, { hdr: 'Error!',
                            msg: 'Failed to update inventory varaibles. PUT returned status: ' + status
                        });
                    });
            });

            Rest.setUrl(defaultUrl);
            Rest.post(data)
                .success(function (data) {
                    var inventory_id = data.id;
                    if ($scope.variables) {
                        $scope.$emit('UpdateInventoryVariables', data);
                    } else {
                        Wait('stop');
                        $location.path('/inventories/' + inventory_id + '/');
                    }
                })
                .error(function (data, status) {
                    ProcessErrors( $scope, data, status, form, { hdr: 'Error!',
                        msg: 'Failed to add new inventory. Post returned status: ' + status });
                });
        } catch (err) {
            Wait('stop');
            Alert("Error", "Error parsing inventory variables. Parser returned: " + err);
        }

    };

    // Reset
    $scope.formReset = function () {
        generator.reset();
    };
}

InventoriesAdd.$inject = ['$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'InventoryForm', 'GenerateForm',
    'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'ReturnToCaller', 'ClearScope', 'GenerateList', 'OrganizationList', 'SearchInit',
    'PaginateInit', 'LookUpInit', 'GetBasePath', 'ParseTypeChange', 'Wait', 'ToJSON'
];

export function InventoriesEdit($scope, $rootScope, $compile, $location, $log, $routeParams, InventoryForm, GenerateForm, Rest,
    Alert, ProcessErrors, LoadBreadCrumbs, ReturnToCaller, ClearScope, GenerateList, OrganizationList, SearchInit, PaginateInit,
    LookUpInit, GetBasePath, ParseTypeChange, Wait, ToJSON, ParseVariableString, Stream) {

    ClearScope();

    // Inject dynamic view
    var defaultUrl = GetBasePath('inventory'),
        form = InventoryForm,
        generator = GenerateForm,
        inventory_id = $routeParams.inventory_id,
        master = {},
        fld, json_data, data;

    form.well = true;
    form.formLabelSize = null;
    form.formFieldSize = null;

    generator.inject(form, { mode: 'edit', related: false, scope: $scope });

    generator.reset();
    LoadBreadCrumbs();

    // $scope.parseType = 'yaml';
    // ParseTypeChange({
    //     scope: $scope,
    //     variable: 'variables',
    //     parse_variable: 'parseType',
    //     field_id: 'inventory_variables'
    // });

    // LookUpInit({
    //     scope:  $scope,
    //     form: form,
    //     current_item: ($routeParams.organization_id) ? $routeParams.organization_id : null,
    //     list: OrganizationList,
    //     field: 'organization',
    //     input_type: 'radio'
    // });
    Wait('start');
    Rest.setUrl(GetBasePath('inventory') + inventory_id + '/');
    Rest.get()
        .success(function (data) {
            var fld;
            for (fld in form.fields) {
                if (fld === 'variables') {
                    $scope.variables = ParseVariableString(data.variables);
                    master.variables = $scope.variables;
                } else if (fld === 'inventory_name') {
                  $scope[fld] = data.name;
                    master[fld] = $scope[fld];
                } else if (fld === 'inventory_description') {
                  $scope[fld] = data.description;
                    master[fld] = $scope[fld];
                } else if (data[fld]) {
                  $scope[fld] = data[fld];
                    master[fld] = $scope[fld];
                }
                if (form.fields[fld].sourceModel && data.summary_fields &&
                    data.summary_fields[form.fields[fld].sourceModel]) {
                      $scope[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] =
                        data.summary_fields[form.fields[fld].sourceModel][form.fields[fld].sourceField];
                    master[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] =
                        data.summary_fields[form.fields[fld].sourceModel][form.fields[fld].sourceField];
                }
            }
            Wait('stop');
            $scope.parseType = 'yaml';
            ParseTypeChange({
                scope: $scope,
                variable: 'variables',
                parse_variable: 'parseType',
                field_id: 'inventory_variables'
            });
            LookUpInit({
                scope: $scope,
                form: form,
                current_item: $scope.organization,
                list: OrganizationList,
                field: 'organization',
                input_type: 'radio'
            });
        })
        .error(function (data, status) {
            ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                msg: 'Failed to get inventory: ' + inventory_id + '. GET returned: ' + status });
        });
    // Save
    $scope.formSave = function () {
      Wait('start');

      // Make sure we have valid variable data
      json_data = ToJSON($scope.parseType, $scope.variables);

      data = {};
      for (fld in form.fields) {
          if (fld !== 'variables') {
              if (form.fields[fld].realName) {
                  data[form.fields[fld].realName] = $scope[fld];
              } else {
                  data[fld] = $scope[fld];
              }
          }
      }

      if ($scope.removeUpdateInventoryVariables) {
        $scope.removeUpdateInventoryVariables();
      }
      $scope.removeUpdateInventoryVariables = $scope.$on('UpdateInventoryVariables', function(e, data) {
          Rest.setUrl(data.related.variable_data);
          Rest.put(json_data)
              .success(function () {
                  Wait('stop');
                  $location.path('/inventories/');
              })
              .error(function (data, status) {
                  ProcessErrors($scope, data, status, form, { hdr: 'Error!',
                      msg: 'Failed to update inventory varaibles. PUT returned status: ' + status
                  });
              });
      });

      Rest.setUrl(defaultUrl + inventory_id + '/');
      Rest.put(data)
          .success(function (data) {
              if ($scope.variables) {
                $scope.$emit('UpdateInventoryVariables', data);
              } else {
                $location.path('/inventories/');
              }
          })
          .error(function (data, status) {
              ProcessErrors($scope, data, status, form, { hdr: 'Error!',
                  msg: 'Failed to update inventory. PUT returned status: ' + status });
          });
    };

    $scope.showActivity = function () {
        Stream({ scope:  $scope });
    };

    // Reset
    $scope.formReset = function () {
        generator.reset();
        for (var fld in master) {
            $scope[fld] = master[fld];
        }
        $scope.parseType = 'yaml';
        ParseTypeChange({
            scope: $scope,
            variable: 'variables',
            parse_variable: 'parseType',
            field_id: 'inventory_variables'
        });
    };
}

InventoriesEdit.$inject = ['$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'InventoryForm', 'GenerateForm',
    'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'ReturnToCaller', 'ClearScope', 'GenerateList', 'OrganizationList', 'SearchInit',
    'PaginateInit', 'LookUpInit', 'GetBasePath', 'ParseTypeChange', 'Wait', 'ToJSON', 'ParseVariableString', 'Stream'
];



export function InventoriesManage ($log, $scope, $location, $routeParams, $compile, GenerateList, ClearScope, Empty, Wait, Rest, Alert, LoadBreadCrumbs, GetBasePath, ProcessErrors,
    Breadcrumbs, InventoryGroups, InjectHosts, Find, HostsReload, SearchInit, PaginateInit, GetSyncStatusMsg, GetHostsStatusMsg, GroupsEdit, InventoryUpdate,
    GroupsCancelUpdate, ViewUpdateStatus, GroupsDelete, Store, HostsEdit, HostsDelete, EditInventoryProperties, ToggleHostEnabled, Stream, ShowJobSummary,
    InventoryGroupsHelp, HelpDialog, ViewJob, WatchInventoryWindowResize, GetHostContainerRows, GetGroupContainerRows, GetGroupContainerHeight,
    GroupsCopy, HostsCopy, Socket)
{

    var PreviousSearchParams,
        url,
        hostScope = $scope.$new(),
        io;

    ClearScope();

    $scope.group_breadcrumbs = [{
        name: '',
        id: 0,
        description: '',
        show: true,
        ngicon: null,
        has_children: false,
        related: {},
        active_class: 'active',
        show_failures: false
    }];

    /**/

    $scope.refreshHostsOnGroupRefresh = false;
    $scope.selected_group_id = null;

    Wait('start');


    if ($scope.removeHostReloadComplete) {
        $scope.removeHostReloadComplete();
    }
    $scope.removeHostReloadComplete = $scope.$on('HostReloadComplete', function() {
        if ($scope.initial_height) {
            var host_height = $('#hosts-container .well').height(),
                group_height = $('#group-list-container .well').height(),
                new_height;

            if (host_height > group_height) {
                new_height = host_height - (host_height - group_height);
            }
            else if (host_height < group_height) {
                new_height = host_height + (group_height - host_height);
            }
            if (new_height) {
                $('#hosts-container .well').height(new_height);
            }
            $scope.initial_height = null;
        }
    });

    if ($scope.removeRowCountReady) {
        $scope.removeRowCountReady();
    }
    $scope.removeRowCountReady = $scope.$on('RowCountReady', function(e, rows) {
        // Add hosts view
        $scope.show_failures = false;
        InjectHosts({
            group_scope: $scope,
            host_scope: hostScope,
            inventory_id: $scope.inventory.id,
            tree_id: null,
            group_id: null,
            pageSize: rows
        });

        SearchInit({ scope: $scope, set: 'groups', list: InventoryGroups, url: $scope.inventory.related.root_groups });
        PaginateInit({ scope: $scope, list: InventoryGroups , url: $scope.inventory.related.root_groups, pageSize: rows });
        $scope.search(InventoryGroups.iterator, null, true);
    });

    if ($scope.removeInventoryLoaded) {
        $scope.removeInventoryLoaded();
    }
    $scope.removeInventoryLoaded = $scope.$on('InventoryLoaded', function() {
        var e, rows;

        LoadBreadCrumbs({
            path: $location.path(),
            title: '{{ inventory.name }}'
        });
        $scope.group_breadcrumbs[0].name = $scope.inventory.name;

        // Build page breadcrumbs
        e = angular.element(document.getElementById('breadcrumbs'));
        e.html(Breadcrumbs({ list: InventoryGroups, mode: 'edit' }));
        $compile(e)($scope);

        // Add groups view
        GenerateList.inject(InventoryGroups, {
            mode: 'edit',
            id: 'group-list-container',
            breadCrumbs: false,
            searchSize: 'col-lg-6 col-md-6 col-sm-6',
            scope: $scope
        });

        if ($(window).width() > 1210) {
            $scope.initial_height = GetGroupContainerHeight();
            $('#groups-container .list-table-container').height($scope.initial_height);
            rows = GetGroupContainerRows();
        }
        else {
            rows = 20;
        }
        hostScope.host_page_size = rows;
        $scope.group_page_size = rows;

        $scope.show_failures = false;
        InjectHosts({
            group_scope: $scope,
            host_scope: hostScope,
            inventory_id: $scope.inventory.id,
            tree_id: null,
            group_id: null,
            pageSize: rows
        });

        // Load data
        SearchInit({ scope: $scope, set: 'groups', list: InventoryGroups, url: $scope.inventory.related.root_groups });
        PaginateInit({ scope: $scope, list: InventoryGroups , url: $scope.inventory.related.root_groups, pageSize: rows });
        $scope.search(InventoryGroups.iterator, null, true);

        $scope.$emit('WatchUpdateStatus');  // init socket io conneciton and start watching for status updates
    });

    if ($scope.removePostRefresh) {
        $scope.removePostRefresh();
    }
    $scope.removePostRefresh = $scope.$on('PostRefresh', function(e, set) {
        if (set === 'groups') {
            $scope.groups.forEach( function(group, idx) {
                var stat, hosts_status;
                stat = GetSyncStatusMsg({
                    status: group.summary_fields.inventory_source.status,
                    has_inventory_sources: group.has_inventory_sources,
                    source: ( (group.summary_fields.inventory_source) ? group.summary_fields.inventory_source.source : null )
                }); // from helpers/Groups.js
                $scope.groups[idx].status_class = stat['class'];
                $scope.groups[idx].status_tooltip = stat.tooltip;
                $scope.groups[idx].launch_tooltip = stat.launch_tip;
                $scope.groups[idx].launch_class = stat.launch_class;
                hosts_status = GetHostsStatusMsg({
                    active_failures: group.hosts_with_active_failures,
                    total_hosts: group.total_hosts,
                    inventory_id: $scope.inventory.id,
                    group_id: group.id
                }); // from helpers/Groups.js
                $scope.groups[idx].hosts_status_tip = hosts_status.tooltip;
                $scope.groups[idx].show_failures = hosts_status.failures;
                $scope.groups[idx].hosts_status_class = hosts_status['class'];

                $scope.groups[idx].source = (group.summary_fields.inventory_source) ? group.summary_fields.inventory_source.source : null;
                $scope.groups[idx].status = (group.summary_fields.inventory_source) ? group.summary_fields.inventory_source.status : null;

            });
            if ($scope.refreshHostsOnGroupRefresh) {
                $scope.refreshHostsOnGroupRefresh = false;
                HostsReload({
                    scope: hostScope,
                    group_id: $scope.selected_group_id,
                    inventory_id: $scope.inventory.id,
                    pageSize: hostScope.host_page_size
                });
            }
            else {
                Wait('stop');
            }

            WatchInventoryWindowResize({
                group_scope: $scope,
                host_scope: hostScope
            });

        }
    });

    // Load Inventory
    url = GetBasePath('inventory') + $routeParams.inventory_id + '/';
    Rest.setUrl(url);
    Rest.get()
        .success(function (data) {
            $scope.inventory = data;
            $scope.$emit('InventoryLoaded');
        })
        .error(function (data, status) {
            ProcessErrors($scope, data, status, null, { hdr: 'Error!', msg: 'Failed to retrieve inventory: ' + $routeParams.inventory_id +
                ' GET returned status: ' + status });
        });

    // start watching for real-time updates
    if ($scope.removeWatchUpdateStatus) {
        $scope.removeWatchUpdateStatus();
    }
    $scope.removeWatchUpdateStatus = $scope.$on('WatchUpdateStatus', function() {
        io = Socket({ scope: $scope, endpoint: "jobs" });
        io.init();
        $log.debug('Watching for job updates: ');
        io.on("status_changed", function(data) {
            var stat, group;
            if (data.group_id) {
                group = Find({ list: $scope.groups, key: 'id', val: data.group_id });
                if (data.status === "failed" || data.status === "successful") {
                    if (data.group_id === $scope.selected_group_id || group) {
                        // job completed, fefresh all groups
                        $log.debug('Update completed. Refreshing the tree.');
                        $scope.refreshGroups();
                    }
                }
                else if (group) {
                    // incremental update, just update
                    $log.debug('Status of group: ' + data.group_id + ' changed to: ' + data.status);
                    stat = GetSyncStatusMsg({
                        status: data.status,
                        has_inventory_sources: group.has_inventory_sources,
                        source: group.source
                    });
                    $log.debug('changing tooltip to: ' + stat.tooltip);
                    group.status = data.status;
                    group.status_class = stat['class'];
                    group.status_tooltip = stat.tooltip;
                    group.launch_tooltip = stat.launch_tip;
                    group.launch_class = stat.launch_class;
                }
            }
        });
    });

    // Load group on selection
    function loadGroups(url) {
        SearchInit({ scope: $scope, set: 'groups', list: InventoryGroups, url: url });
        PaginateInit({ scope: $scope, list: InventoryGroups , url: url, pageSize: $scope.group_page_size });
        $scope.search(InventoryGroups.iterator, null, true, false, true);
    }

    function setActiveGroupBreadcrumb() {
        $scope.group_breadcrumbs.forEach(function(crumb, idx) {
            $scope.group_breadcrumbs[idx].active_class = '';
        });
        $scope.group_breadcrumbs[$scope.group_breadcrumbs.length - 1].active_class = 'active';
        $scope.refreshHostsOnGroupRefresh = true;
        $scope.selected_group_id = ($scope.group_breadcrumbs[$scope.group_breadcrumbs.length - 1].id === 0) ? null : $scope.group_breadcrumbs[$scope.group_breadcrumbs.length - 1].id;
    }

    $scope.refreshHosts = function() {
        HostsReload({
            scope: hostScope,
            group_id: $scope.selected_group_id,
            inventory_id: $scope.inventory.id,
            pageSize: hostScope.host_page_size
        });
    };

    $scope.refreshGroups = function() {
        $scope.refreshHostsOnGroupRefresh = true;
        $scope.search(InventoryGroups.iterator, null, true, false, true);
    };

    $scope.restoreSearch = function() {
        // Restore search params and related stuff, plus refresh
        // groups and hosts lists
        SearchInit({
            scope: $scope,
            set: PreviousSearchParams.set,
            list: PreviousSearchParams.list,
            url: PreviousSearchParams.defaultUrl,
            iterator: PreviousSearchParams.iterator,
            sort_order: PreviousSearchParams.sort_order,
            setWidgets: false
        });
        $scope.refreshHostsOnGroupRefresh = true;
        $scope.search(InventoryGroups.iterator, null, true, false, true);
    };

    $scope.groupSelect = function(id) {
        var group = Find({ list: $scope.groups, key: 'id', val: id });
        $scope.group_breadcrumbs.push(group);
        setActiveGroupBreadcrumb();
        loadGroups(group.related.children, group.id);
    };

    $scope.breadcrumbGroupSelect = function(id) {
        var i, url;
        $scope.group_breadcrumbs.every(function(crumb, idx) {
            if (crumb.id === id) {
                i = idx;
                return false;
            }
            return true;
        });
        $scope.group_breadcrumbs = $scope.group_breadcrumbs.slice(0,i + 1);
        if (id > 0) {
            url = $scope.group_breadcrumbs[$scope.group_breadcrumbs.length - 1].related.children;
        }
        else {
            url = $scope.inventory.related.root_groups;
        }
        setActiveGroupBreadcrumb();
        loadGroups(url);
    };

    $scope.createGroup = function () {
        PreviousSearchParams = Store('group_current_search_params');
        GroupsEdit({
            scope: $scope,
            inventory_id: $scope.inventory.id,
            group_id: $scope.selected_group_id,
            mode: 'add'
        });
    };

    $scope.editGroup = function (id) {
        PreviousSearchParams = Store('group_current_search_params');
        GroupsEdit({
            scope: $scope,
            inventory_id: $scope.inventory.id,
            group_id: id,
            mode: 'edit'
        });
    };

    // Launch inventory sync
    $scope.updateGroup = function (id) {
        var group = Find({ list: $scope.groups, key: 'id', val: id });
        if (group) {
            if (Empty(group.source)) {
                // if no source, do nothing.
            } else if (group.status === 'updating') {
                Alert('Update in Progress', 'The inventory update process is currently running for group <em>' +
                    group.name + '</em> Click the <i class="fa fa-refresh"></i> button to monitor the status.', 'alert-info');
            } else {
                Wait('start');
                Rest.setUrl(group.related.inventory_source);
                Rest.get()
                    .success(function (data) {
                        InventoryUpdate({
                            scope: $scope,
                            url: data.related.update,
                            group_name: data.summary_fields.group.name,
                            group_source: data.source,
                            group_id: group.id,
                        });
                    })
                    .error(function (data, status) {
                        ProcessErrors($scope, data, status, null, { hdr: 'Error!', msg: 'Failed to retrieve inventory source: ' +
                            group.related.inventory_source + ' GET returned status: ' + status });
                    });
            }
        }
    };

    $scope.cancelUpdate = function (id) {
        GroupsCancelUpdate({ scope: $scope, id: id });
    };

    $scope.viewUpdateStatus = function (id) {
        ViewUpdateStatus({
            scope: $scope,
            group_id: id
        });
    };

    $scope.copyGroup = function(id) {
        PreviousSearchParams = Store('group_current_search_params');
        GroupsCopy({
            scope: $scope,
            group_id: id
        });
    };

    $scope.deleteGroup = function (id) {
        GroupsDelete({
            scope: $scope,
            group_id: id,
            inventory_id: $scope.inventory.id
        });
    };

    $scope.editInventoryProperties = function () {
        // EditInventoryProperties({ scope: $scope, inventory_id: $scope.inventory.id });
        $location.path('/inventories/' + $scope.inventory.id + '/');
    };

    hostScope.createHost = function () {
        HostsEdit({
            host_scope: hostScope,
            group_scope: $scope,
            mode: 'add',
            host_id: null,
            selected_group_id: $scope.selected_group_id,
            inventory_id: $scope.inventory.id
        });
    };

    hostScope.editHost = function (host_id) {
        HostsEdit({
            host_scope: hostScope,
            group_scope: $scope,
            mode: 'edit',
            host_id: host_id,
            inventory_id: $scope.inventory.id
        });
    };

    hostScope.deleteHost = function (host_id, host_name) {
        HostsDelete({
            parent_scope: $scope,
            host_scope: hostScope,
            host_id: host_id,
            host_name: host_name
        });
    };

    hostScope.copyHost = function(id) {
        PreviousSearchParams = Store('group_current_search_params');
        HostsCopy({
            group_scope: $scope,
            host_scope: hostScope,
            host_id: id
        });
    };

    /*hostScope.restoreSearch = function() {
        SearchInit({
            scope: hostScope,
            set: PreviousSearchParams.set,
            list: PreviousSearchParams.list,
            url: PreviousSearchParams.defaultUrl,
            iterator: PreviousSearchParams.iterator,
            sort_order: PreviousSearchParams.sort_order,
            setWidgets: false
        });
        hostScope.search('host');
    };*/

    hostScope.toggleHostEnabled = function (host_id, external_source) {
        ToggleHostEnabled({
            parent_scope: $scope,
            host_scope: hostScope,
            host_id: host_id,
            external_source: external_source
        });
    };

    $scope.showGroupActivity = function () {
        var url, title, group;
        if ($scope.selected_group_id) {
            $scope.group_breadcrumbs.every(function(crumb) {
                if (crumb.id === $scope.selected_group_id) {
                    group = crumb;
                    return false;
                }
                return true;
            });
            url = GetBasePath('activity_stream') + '?group__id=' + $scope.selected_group_id;
            title = 'Showing all activities for group ' + group.name;
        } else {
            title = 'Showing all activities for all ' + $scope.inventory.name + ' groups';
            url = GetBasePath('activity_stream') + '?group__inventory__id=' + $scope.inventory.id;
        }
        Stream({
            scope: $scope,
            inventory_name: $scope.inventory.name,
            url: url,
            title: title,
            search_iterator: 'group',
            onClose: 'GroupStreamClosed'
        });
    };

    if ($scope.removeGroupStreamClosed) {
        $scope.removeGroupStreamClosed();
    }
    $scope.removeGroupStreamClosed = $scope.$on('GroupStreamClosed', function() {
        $scope.refreshGroups();
    });

    hostScope.showHostActivity = function () {
        var url, title;
        title = 'Showing all activities for all ' + $scope.inventory.name + ' hosts';
        url = GetBasePath('activity_stream') + '?host__inventory__id=' + $scope.inventory.id;
        Stream({
            scope: hostScope,
            inventory_name: $scope.inventory.name,
            url: url,
            title: title,
            search_iterator: 'host',
            onClose: 'HostStreamClosed'
        });
    };

    if (hostScope.removeHostStreamClosed) {
        hostScope.removeHostStreamClosed();
    }
    hostScope.removeHostStreamClosed = hostScope.$on('HostStreamClosed', function() {
        $scope.refreshGroups();
    });

    hostScope.showJobSummary = function (job_id) {
        ShowJobSummary({
            job_id: job_id
        });
    };

    $scope.showGroupHelp = function (params) {
        var opts = {
            defn: InventoryGroupsHelp
        };
        if (params) {
            opts.autoShow = params.autoShow || false;
        }
        HelpDialog(opts);
    };

    $scope.viewJob = function(id) {
        ViewJob({ scope: $scope, id: id });
    };

    $scope.showHosts = function (group_id, show_failures) {
        // Clicked on group
        if (group_id !== null) {
            Wait('start');
            hostScope.show_failures = show_failures;
            $scope.groupSelect(group_id);
            hostScope.hosts = [];
            $scope.show_failures = show_failures; // turn on failed hosts filter in hosts view
        } else {
            Wait('stop');
        }
    };

    if ($scope.removeGroupDeleteCompleted) {
        $scope.removeGroupDeleteCompleted();
    }
    $scope.removeGroupDeleteCompleted = $scope.$on('GroupDeleteCompleted', function() {
        $scope.refreshGroups();
    });
}

InventoriesManage.$inject = ['$log', '$scope', '$location', '$routeParams', '$compile', 'GenerateList', 'ClearScope', 'Empty', 'Wait', 'Rest', 'Alert', 'LoadBreadCrumbs',
    'GetBasePath', 'ProcessErrors', 'Breadcrumbs', 'InventoryGroups', 'InjectHosts', 'Find', 'HostsReload', 'SearchInit', 'PaginateInit', 'GetSyncStatusMsg',
    'GetHostsStatusMsg', 'GroupsEdit', 'InventoryUpdate', 'GroupsCancelUpdate', 'ViewUpdateStatus', 'GroupsDelete', 'Store', 'HostsEdit', 'HostsDelete',
    'EditInventoryProperties', 'ToggleHostEnabled', 'Stream', 'ShowJobSummary', 'InventoryGroupsHelp', 'HelpDialog', 'ViewJob', 'WatchInventoryWindowResize',
    'GetHostContainerRows', 'GetGroupContainerRows', 'GetGroupContainerHeight', 'GroupsCopy', 'HostsCopy', 'Socket'
    ];
