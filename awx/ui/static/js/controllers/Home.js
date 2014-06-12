/************************************
 * Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *
 *  Home.js
 *
 *  Controller functions for Home tab
 *
 */

'use strict';

function Home($scope, $compile, $routeParams, $rootScope, $location, Wait, ObjectCount, JobStatus, InventorySyncStatus, SCMSyncStatus,
    ClearScope, Stream, Rest, GetBasePath, ProcessErrors, Button) {

    ClearScope('home');

    var buttons, html, e, waitCount, loadedCount;

    // Add buttons to the top of the Home page. We're using lib/ansible/generator_helpers.js-> Buttons()
    // to build buttons dynamically and insure all styling and icons match the rest of the application.
    buttons = {
        refresh: {
            mode: 'all',
            awToolTip: "Refresh the page",
            ngClick: "refresh()"
        },
        stream: {
            ngClick: "showActivity()",
            awToolTip: "View Activity Stream",
            mode: 'all'
        }
    };

    html = Button({
        btn: buttons.refresh,
        action: 'refresh',
        toolbar: true
    });

    html += Button({
        btn: buttons.stream,
        action: 'stream',
        toolbar: true
    });

    e = angular.element(document.getElementById('home-list-actions'));
    e.html(html);
    $compile(e)($scope);

    waitCount = 4;
    loadedCount = 0;

    if (!$routeParams.login) {
        // If we're not logging in, start the Wait widget. Otherwise, it's already running.
        Wait('start');
    }

    if ($scope.removeWidgetLoaded) {
        $scope.removeWidgetLoaded();
    }
    $scope.removeWidgetLoaded = $scope.$on('WidgetLoaded', function () {
        // Once all the widgets report back 'loaded', turn off Wait widget
        loadedCount++;
        if (loadedCount === waitCount) {
            Wait('stop');
        }
    });

    if ($scope.removeDashboardReady) {
        $scope.removeDashboardReady();
    }
    $scope.removeDashboardReady = $scope.$on('dashboardReady', function (e, data) {
        JobStatus({
            scope: $scope,
            target: 'container1',
            dashboard: data
        });
        InventorySyncStatus({
            scope: $scope,
            target: 'container2',
            dashboard: data
        });
        SCMSyncStatus({
            scope: $scope,
            target: 'container4',
            dashboard: data
        });
        ObjectCount({
            scope: $scope,
            target: 'container3',
            dashboard: data
        });
    });

    $scope.showActivity = function () {
        Stream({
            scope: $scope
        });
    };

    $scope.refresh = function () {
        Wait('start');
        loadedCount = 0;
        Rest.setUrl(GetBasePath('dashboard'));
        Rest.get()
            .success(function (data) {
                $scope.$emit('dashboardReady', data);
            })
            .error(function (data, status) {
                Wait('stop');
                ProcessErrors($scope, data, status, null, { hdr: 'Error!', msg: 'Failed to get dashboard: ' + status });
            });
    };

    $scope.refresh();

}

Home.$inject = ['$scope', '$compile', '$routeParams', '$rootScope', '$location', 'Wait', 'ObjectCount', 'JobStatus', 'InventorySyncStatus',
    'SCMSyncStatus', 'ClearScope', 'Stream', 'Rest', 'GetBasePath', 'ProcessErrors', 'Button'
];


function HomeGroups($log, $scope, $filter, $compile, $location, $routeParams, LogViewer, HomeGroupList, GenerateList, ProcessErrors, LoadBreadCrumbs, ReturnToCaller, ClearScope,
    GetBasePath, SearchInit, PaginateInit, FormatDate, GetHostsStatusMsg, GetSyncStatusMsg, ViewUpdateStatus, Stream, GroupsEdit, Wait,
    Alert, Rest, Empty, InventoryUpdate, Find, GroupsCancelUpdate, Store, Socket) {

    ClearScope('htmlTemplate'); //Garbage collection. Don't leave behind any listeners/watchers from the prior
    //scope.

    var generator = GenerateList,
        list = HomeGroupList,
        defaultUrl = GetBasePath('groups'),
        scope = $scope,
        modal_scope = $scope.$new(),
        opt, PreviousSearchParams,
        io;

    generator.inject(list, { mode: 'edit', scope: scope });

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
        elem.attr({ "aw-pop-over": html, "data-title": title, "data-placement": "right" });
        $compile(elem)(scope);
        elem.on('shown.bs.popover', function() {
            $('.popover').each(function() {
                $compile($(this))(scope);  //make nested directives work!
            });
            $('.popover-content, .popover-title').click(function() {
                elem.popover('hide');
            });
        });
        elem.popover('show');
    }

    if (scope.removePostRefresh) {
        scope.removePostRefresh();
    }
    scope.removePostRefresh = scope.$on('PostRefresh', function () {
        var i, hosts_status, stat;
        for (i = 0; i < scope.home_groups.length; i++) {
            scope.home_groups[i].inventory_name = scope.home_groups[i].summary_fields.inventory.name;

            stat = GetSyncStatusMsg({
                status: scope.home_groups[i].summary_fields.inventory_source.status,
                source: scope.home_groups[i].summary_fields.inventory_source.source,
                has_inventory_sources: scope.home_groups[i].has_inventory_sources
            }); // from helpers/Groups.js

            hosts_status = GetHostsStatusMsg({
                active_failures: scope.home_groups[i].hosts_with_active_failures,
                total_hosts: scope.home_groups[i].total_hosts,
                inventory_id: scope.home_groups[i].inventory,
                group_id: scope.home_groups[i].id
            });

            scope.home_groups[i].status_class = stat['class'];
            scope.home_groups[i].status_tooltip = stat.tooltip;
            scope.home_groups[i].launch_tooltip = stat.launch_tip;
            scope.home_groups[i].launch_class = stat.launch_class;
            scope.home_groups[i].hosts_status_tip = hosts_status.tooltip;
            scope.home_groups[i].show_failures = hosts_status.failures;
            scope.home_groups[i].hosts_status_class = hosts_status['class'];
            scope.home_groups[i].status = scope.home_groups[i].summary_fields.inventory_source.status;
            scope.home_groups[i].source = (scope.home_groups[i].summary_fields.inventory_source) ?
                scope.home_groups[i].summary_fields.inventory_source.source : null;
        }
    });

    SearchInit({
        scope: scope,
        set: 'home_groups',
        list: list,
        url: defaultUrl
    });

    PaginateInit({
        scope: scope,
        list: list,
        url: defaultUrl
    });

    // Process search params
    if ($routeParams.name) {
        scope[list.iterator + 'InputDisable'] = false;
        scope[list.iterator + 'SearchValue'] = $routeParams.name;
        scope[list.iterator + 'SearchField'] = 'name';
        scope[list.iterator + 'SearchFieldLabel'] = list.fields.name.label;
        scope[list.iterator + 'SearchSelectValue'] = null;
    }

    if ($routeParams.id) {
        scope[list.iterator + 'InputDisable'] = false;
        scope[list.iterator + 'SearchValue'] = $routeParams.id;
        scope[list.iterator + 'SearchField'] = 'id';
        scope[list.iterator + 'SearchFieldLabel'] = list.fields.id.label;
        scope[list.iterator + 'SearchSelectValue'] = null;
    }

    if ($routeParams.has_active_failures) {
        scope[list.iterator + 'InputDisable'] = true;
        scope[list.iterator + 'SearchValue'] = $routeParams.has_active_failures;
        scope[list.iterator + 'SearchField'] = 'has_active_failures';
        scope[list.iterator + 'SearchFieldLabel'] = list.fields.has_active_failures.label;
        scope[list.iterator + 'SearchSelectValue'] = ($routeParams.has_active_failures === 'true') ? { value: 1 } : { value: 0 };
    }

    if ($routeParams.status && !$routeParams.source) {
        scope[list.iterator + 'SearchField'] = 'last_update_failed';
        scope[list.iterator + 'SearchFieldLabel'] = list.fields.last_update_failed.label;
        scope[list.iterator + 'SelectShow'] = false;
        scope[list.iterator + 'SearchValue'] = 'failed';
        scope[list.iterator + 'SearchSelectValue'] = { value: 'failed' };

        //scope[list.iterator + 'SelectShow'] = true;
        //scope[list.iterator + 'SearchSelectOpts'] = list.fields.status.searchOptions;
        //scope[list.iterator + 'SearchFieldLabel'] = list.fields.status.label.replace(/<br\>/g, ' ');
        //for (opt in list.fields.status.searchOptions) {
        //    if (list.fields.status.searchOptions[opt].value === $routeParams.status) {
        //        scope[list.iterator + 'SearchSelectValue'] = list.fields.status.searchOptions[opt];
        //        break;
        //    }
        //}
    }

    if ($routeParams.source) {
        scope[list.iterator + 'SearchField'] = 'source';
        scope[list.iterator + 'SelectShow'] = true;
        scope[list.iterator + 'SearchSelectOpts'] = list.fields.source.searchOptions;
        scope[list.iterator + 'SearchFieldLabel'] = list.fields.source.label.replace(/<br\>/g, ' ');
        for (opt in list.fields.source.searchOptions) {
            if (list.fields.source.searchOptions[opt].value === $routeParams.source) {
                scope[list.iterator + 'SearchSelectValue'] = list.fields.source.searchOptions[opt];
                break;
            }
        }

        if ($routeParams.status) {
            scope[list.iterator + 'ExtraParms'] = '&inventory_source__status__icontains=' + $routeParams.status;
        }
    }

    if ($routeParams.has_external_source) {
        scope[list.iterator + 'SearchField'] = 'has_external_source';
        scope[list.iterator + 'SearchValue'] = list.fields.has_external_source.searchValue;
        scope[list.iterator + 'InputDisable'] = true;
        scope[list.iterator + 'SearchType'] = 'in';
        scope[list.iterator + 'SearchFieldLabel'] = list.fields.has_external_source.label;
    }

    if ($routeParams.inventory_source__id) {
        scope[list.iterator + 'SearchField'] = 'inventory_source';
        scope[list.iterator + 'SearchValue'] = $routeParams.inventory_source__id;
        scope[list.iterator + 'SearchFieldLabel'] = 'Source ID';
    }

    scope.search(list.iterator);

    scope.$emit('WatchUpdateStatus');  // Start watching for live updates

    LoadBreadCrumbs();

    io = Socket({ scope: $scope, endpoint: "jobs" });
    io.init();
    $log.debug('Watching for job updates: ');
    io.on("status_changed", function(data) {
        var stat, group;
        if (data.group_id) {
            group = Find({ list: scope[list.name], key: 'id', val: data.group_id });
            if (group && (data.status === "failed" || data.status === "successful")) {
                // job completed, fefresh all groups
                $log.debug('Update completed. Refreshing the list');
                scope.refresh();
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

    scope.showActivity = function () {
        Stream({
            scope: scope
        });
    };

    scope.editGroup = function (group_id, inventory_id) {
        PreviousSearchParams = Store('group_current_search_params');
        GroupsEdit({
            scope: scope,
            group_id: group_id,
            inventory_id: inventory_id,
            groups_reload: false,
            mode: 'edit'
        });
    };

    scope.restoreSearch = function() {
        SearchInit({
            scope: scope,
            set: PreviousSearchParams.set,
            list: PreviousSearchParams.list,
            url: PreviousSearchParams.defaultUrl,
            iterator: PreviousSearchParams.iterator,
            sort_order: PreviousSearchParams.sort_order,
            setWidgets: false
        });
        scope.refresh();
    };

    scope.viewUpdateStatus = function (id) {
        scope.groups = scope.home_groups;
        ViewUpdateStatus({
            scope: scope,
            group_id: id
        });
    };

    // Launch inventory sync
    scope.updateGroup = function (id) {
        var group = Find({ list: scope.home_groups, key: 'id', val: id });
        if (group) {
            if (Empty(group.source)) {
                // if no source, do nothing.
            } else if (group.status === 'updating') {
                Alert('Update in Progress', 'The inventory update process is currently running for group <em>' +
                    group.name + '</em>. Use the Refresh button to monitor the status.', 'alert-info');
            } else {
                Wait('start');
                Rest.setUrl(group.related.inventory_source);
                Rest.get()
                    .success(function (data) {
                        InventoryUpdate({
                            scope: scope,
                            url: data.related.update,
                            group_name: data.summary_fields.group.name,
                            group_source: data.source,
                            tree_id: group.id,
                            group_id: group.id
                        });
                    })
                    .error(function (data, status) {
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                            msg: 'Failed to retrieve inventory source: ' + group.related.inventory_source + ' POST returned status: ' + status
                        });
                    });
            }
        }
    };

    scope.refresh = function () {
        scope.search(list.iterator);
    };


    if (scope.removeHostSummaryReady) {
        scope.removeHostSummaryReady();
    }
    scope.removeHostSummaryReady = scope.$on('HostSummaryReady', function(e, event, data) {
        var html, title = "Recent Jobs", url = GetBasePath('jobs');
        Wait('stop');
        if (data.length > 0) {
            html = "<table class=\"table table-condensed flyout\" style=\"width: 100%\">\n";
            html += "<thead>\n";
            html += "<tr>";
            html += "<th>Status</th>";
            html += "<th>View</th>";
            html += "<th>Name</th>";
            html += "</tr>\n";
            html += "</thead>\n";
            html += "<tbody>\n";
            data.forEach(function(row) {
                html += "<tr>\n";
                html += "<td><a ng-click=\"viewJob('" + url + row.id + "/')\" " + "aw-tool-tip=\"" + row.status.charAt(0).toUpperCase() + row.status.slice(1) +
                    ". Click for details\" aw-tip-placement=\"top\"><i class=\"fa icon-job-" +
                    row.status + "\"></i></a></td>\n";
                //html += "<td>" + ($filter('date')(row.finished,'MM/dd HH:mm:ss')).replace(/ /,'<br />') + "</td>";
                html += "<td><a href=\"/#/job_events/" + row.id + "\">Events</a><br />" +
                    "<a href=\"/#/job_host_summaries/" + row.id + "\">Hosts</a></td>";
                html += "<td><a href=\"\" ng-click=\"viewJob('" + url + row.id + "/')\" >" + ellipsis(row.name) + "</a></td>";
                html += "</tr>\n";
            });
            html += "</tbody>\n";
            html += "</table>\n";
            html += "<div class=\"popover-footer\"><span class=\"key\">esc</span> or click to close</div>\n";
        }
        else {
            html = "<p>No recent job data available for this inventory.</p>\n" +
                "<div class=\"popover-footer\"><span class=\"key\">esc</span> or click to close</div>\n";
        }
        attachElem(event, html, title);
    });

    if (scope.removeGroupSummaryReady) {
        scope.removeGroupSummaryReady();
    }
    scope.removeGroupSummaryReady = scope.$on('GroupSummaryReady', function(e, event, inventory, data) {
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
            html += "<tr>";
            html += "<td><a href=\"\" ng-click=\"viewJob('" + row.related.last_update + "')\" aw-tool-tip=\"" + row.status.charAt(0).toUpperCase() + row.status.slice(1) + ". Click for details\" aw-tip-placement=\"top\"><i class=\"fa icon-job-" + row.status + "\"></i></a></td>";
            html += "<td>" + ($filter('date')(row.last_updated,'MM/dd HH:mm:ss')).replace(/ /,'<br />') + "</td>";
            html += "<td><a href=\"\" ng-click=\"viewJob('" + row.related.last_update + "')\">" + ellipsis(row.summary_fields.group.name) + "</a></td>";
            html += "</tr>\n";
        });
        html += "</tbody>\n";
        html += "</table>\n";
        html += "<div class=\"popover-footer\"><span class=\"key\">esc</span> or click to close</div>\n";
        title = "Sync Status";
        attachElem(event, html, title);
    });

    scope.showGroupSummary = function(event, id) {
        var group, status;
        if (!Empty(id)) {
            group = Find({ list: scope.home_groups, key: 'id', val: id });
            status = group.summary_fields.inventory_source.status;
            if (status === 'running' || status === 'failed' || status === 'error' || status === 'successful') {
                Wait('start');
                Rest.setUrl(group.related.inventory_sources + '?or__source=ec2&or__source=rax&order_by=-last_job_run&page_size=5');
                Rest.get()
                    .success(function(data) {
                        scope.$emit('GroupSummaryReady', event, group, data);
                    })
                    .error(function(data, status) {
                        ProcessErrors( scope, data, status, null, { hdr: 'Error!',
                            msg: 'Call to ' + group.related.inventory_sources + ' failed. GET returned status: ' + status
                        });
                    });
            }
        }
    };

    scope.showHostSummary = function(event, id) {
        var url, jobs = [];
        if (!Empty(id)) {
            Wait('start');
            url = GetBasePath('hosts') + "?groups__id=" + id + "&last_job__isnull=false&order_by=-last_job&page_size=5";
            Rest.setUrl(url);
            Rest.get()
                .success( function(data) {
                    data.results.forEach(function(host) {
                        var found = false;
                        jobs.every(function(existing_job) {
                            if (host.last_job === existing_job.id) {
                                found = true;
                                return false;
                            }
                            return true;
                        });
                        if (!found) {
                            jobs.push({
                                id: host.last_job,
                                status: host.summary_fields.last_job.status,
                                name: host.summary_fields.last_job.name
                            });
                        }
                    });
                    scope.$emit('HostSummaryReady', event, jobs);
                })
                .error( function(data, status) {
                    ProcessErrors( scope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + ' failed. GET returned: ' + status
                    });
                });
        }
    };

    scope.viewJob = function(url) {
        LogViewer({
            scope: modal_scope,
            url: url
        });
    };

    scope.cancelUpdate = function(id) {
        var group = Find({ list: scope.home_groups, key: 'id', val: id });
        GroupsCancelUpdate({ scope: scope, group: group });
    };


}

HomeGroups.$inject = ['$log', '$scope', '$filter', '$compile', '$location', '$routeParams', 'LogViewer', 'HomeGroupList', 'GenerateList', 'ProcessErrors', 'LoadBreadCrumbs', 'ReturnToCaller',
    'ClearScope', 'GetBasePath', 'SearchInit', 'PaginateInit', 'FormatDate', 'GetHostsStatusMsg', 'GetSyncStatusMsg', 'ViewUpdateStatus',
    'Stream', 'GroupsEdit', 'Wait', 'Alert', 'Rest', 'Empty', 'InventoryUpdate', 'Find', 'GroupsCancelUpdate', 'Store', 'Socket'
];


function HomeHosts($scope, $location, $routeParams, HomeHostList, GenerateList, ProcessErrors, LoadBreadCrumbs, ReturnToCaller, ClearScope,
    GetBasePath, SearchInit, PaginateInit, FormatDate, SetStatus, ToggleHostEnabled, HostsEdit, Stream, Find, ShowJobSummary, ViewJob) {

    ClearScope('htmlTemplate'); //Garbage collection. Don't leave behind any listeners/watchers from the prior
    //scope.

    var generator = GenerateList,
        list = HomeHostList,
        defaultUrl = GetBasePath('hosts');

    if ($scope.removePostRefresh) {
        $scope.removePostRefresh();
    }
    $scope.removePostRefresh = $scope.$on('PostRefresh', function () {
        for (var i = 0; i < $scope.hosts.length; i++) {
            $scope.hosts[i].inventory_name = $scope.hosts[i].summary_fields.inventory.name;
            //SetHostStatus($scope['hosts'][i]);
            SetStatus({
                $scope: $scope,
                host: $scope.hosts[i]
            });
        }

        generator.inject(list, { mode: 'edit', scope: $scope });

    });

    SearchInit({
        scope: $scope,
        set: 'hosts',
        list: list,
        url: defaultUrl
    });

    PaginateInit({
        scope: $scope,
        list: list,
        url: defaultUrl
    });

    // Process search params
    if ($routeParams.name) {
        $scope[HomeHostList.iterator + 'InputDisable'] = false;
        $scope[HomeHostList.iterator + 'SearchValue'] = $routeParams.name;
        $scope[HomeHostList.iterator + 'SearchField'] = 'name';
        $scope[HomeHostList.iterator + 'SearchFieldLabel'] = list.fields.name.label;
    }

    if ($routeParams.id) {
        $scope[HomeHostList.iterator + 'InputDisable'] = false;
        $scope[HomeHostList.iterator + 'SearchValue'] = $routeParams.id;
        $scope[HomeHostList.iterator + 'SearchField'] = 'id';
        $scope[HomeHostList.iterator + 'SearchFieldLabel'] = list.fields.id.label;
        $scope[HomeHostList.iterator + 'SearchSelectValue'] = null;
    }

    if ($routeParams.has_active_failures) {
        $scope[HomeHostList.iterator + 'InputDisable'] = true;
        $scope[HomeHostList.iterator + 'SearchValue'] = $routeParams.has_active_failures;
        $scope[HomeHostList.iterator + 'SearchField'] = 'has_active_failures';
        $scope[HomeHostList.iterator + 'SearchFieldLabel'] = HomeHostList.fields.has_active_failures.label;
        $scope[HomeHostList.iterator + 'SearchSelectValue'] = ($routeParams.has_active_failures === 'true') ? { value: 1 } : { value: 0 };
    }

    $scope.search(list.iterator);

    LoadBreadCrumbs();

    $scope.viewJob = function(id) {
        ViewJob({ scope: $scope, id: id });
    };

    $scope.showActivity = function () {
        Stream({
            scope: $scope
        });
    };

    $scope.toggleHostEnabled = function (id, sources) {
        ToggleHostEnabled({
            host_id: id,
            external_source: sources,
            scope: $scope
        });
    };

    $scope.editHost = function (host_id) {
        var host = Find({
            list: $scope.hosts,
            key: 'id',
            val: host_id
        });
        if (host) {
            HostsEdit({
                scope: $scope,
                host_id: host_id,
                inventory_id: host.inventory,
                group_id: null,
                hostsReload: false,
                mode: 'edit'
            });
        }
    };

    $scope.showJobSummary = function (job_id) {
        ShowJobSummary({
            job_id: job_id
        });
    };

}

HomeHosts.$inject = ['$scope', '$location', '$routeParams', 'HomeHostList', 'GenerateList', 'ProcessErrors', 'LoadBreadCrumbs', 'ReturnToCaller',
    'ClearScope', 'GetBasePath', 'SearchInit', 'PaginateInit', 'FormatDate', 'SetStatus', 'ToggleHostEnabled', 'HostsEdit', 'Stream',
    'Find', 'ShowJobSummary', 'ViewJob'
];