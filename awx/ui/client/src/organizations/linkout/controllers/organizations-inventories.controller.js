/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', '$rootScope', '$location', '$log',
    '$stateParams', '$compile', '$filter', 'sanitizeFilter', 'Rest', 'Alert', 'InventoryList',
    'generateList', 'Prompt', 'SearchInit', 'PaginateInit', 'ReturnToCaller',
    'ClearScope', 'ProcessErrors', 'GetBasePath', 'Wait', 'Find', 'Empty', '$state',
    function($scope, $rootScope, $location, $log,
        $stateParams, $compile, $filter, sanitizeFilter, Rest, Alert, InventoryList,
        generateList, Prompt, SearchInit, PaginateInit, ReturnToCaller,
        ClearScope, ProcessErrors, GetBasePath, Wait,
        Find, Empty, $state) {

            var list,
                invUrl,
                orgBase = GetBasePath('organizations'),
                generator = generateList;

            // Go out and get the organization
            Rest.setUrl(orgBase + $stateParams.organization_id);
            Rest.get()
                .success(function (data) {
                    // include name of item in listTitle
                    var listTitle = data.name + "<div class='List-titleLockup'></div>INVENTORIES";

                    $scope.$parent.activeCard = parseInt($stateParams.organization_id);
                    $scope.$parent.activeMode = 'inventories';
                    $scope.organization_name = data.name;
                    $scope.org_id = data.id;

                    list = _.cloneDeep(InventoryList);
                    list.emptyListText = "This list is populated by inventories added from the&nbsp;<a ui-sref='inventories.add'>Inventories</a>&nbsp;section";
                    delete list.actions.add;
                    delete list.fieldActions.delete;
                    invUrl = data.related.inventories;
                    list.listTitle = listTitle;
                    list.basePath = invUrl;

                    $scope.orgRelatedUrls = data.related;

                    generator.inject(list, { mode: 'edit', scope: $scope, cancelButton: true });
                    $rootScope.flashMessage = null;

                    SearchInit({
                        scope: $scope,
                        set: 'inventories',
                        list: list,
                        url: invUrl
                    });
                    PaginateInit({
                        scope: $scope,
                        list: list,
                        url: invUrl
                    });

                    if ($stateParams.name) {
                        $scope[InventoryList.iterator + 'InputDisable'] = false;
                        $scope[InventoryList.iterator + 'SearchValue'] = $stateParams.name;
                        $scope[InventoryList.iterator + 'SearchField'] = 'name';
                        $scope[InventoryList.iterator + 'SearchFieldLabel'] = InventoryList.fields.name.label;
                        $scope[InventoryList.iterator + 'SearchSelectValue'] = null;
                    }

                    if ($stateParams.has_active_failures) {
                        $scope[InventoryList.iterator + 'InputDisable'] = true;
                        $scope[InventoryList.iterator + 'SearchValue'] = $stateParams.has_active_failures;
                        $scope[InventoryList.iterator + 'SearchField'] = 'has_active_failures';
                        $scope[InventoryList.iterator + 'SearchFieldLabel'] = InventoryList.fields.has_active_failures.label;
                        $scope[InventoryList.iterator + 'SearchSelectValue'] = ($stateParams.has_active_failures === 'true') ? {
                            value: 1
                        } : {
                            value: 0
                        };
                    }

                    if ($stateParams.has_inventory_sources) {
                        $scope[InventoryList.iterator + 'InputDisable'] = true;
                        $scope[InventoryList.iterator + 'SearchValue'] = $stateParams.has_inventory_sources;
                        $scope[InventoryList.iterator + 'SearchField'] = 'has_inventory_sources';
                        $scope[InventoryList.iterator + 'SearchFieldLabel'] = InventoryList.fields.has_inventory_sources.label;
                        $scope[InventoryList.iterator + 'SearchSelectValue'] = ($stateParams.has_inventory_sources === 'true') ? {
                            value: 1
                        } : {
                            value: 0
                        };
                    }

                    if ($stateParams.inventory_sources_with_failures) {
                        // pass a value of true, however this field actually contains an integer value
                        $scope[InventoryList.iterator + 'InputDisable'] = true;
                        $scope[InventoryList.iterator + 'SearchValue'] = $stateParams.inventory_sources_with_failures;
                        $scope[InventoryList.iterator + 'SearchField'] = 'inventory_sources_with_failures';
                        $scope[InventoryList.iterator + 'SearchFieldLabel'] = InventoryList.fields.inventory_sources_with_failures.label;
                        $scope[InventoryList.iterator + 'SearchType'] = 'gtzero';
                    }

                    $scope.search(list.iterator);
                });

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
                elem.attr({
                    "aw-pop-over": html,
                    "data-popover-title": title,
                    "data-placement": "right" });
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
                        html += "<td>" + ($filter('longDate')(row.finished)).replace(/ /,'<br />') + "</td>";
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
                        html += "<td>" + ($filter('longDate')(row.last_updated)).replace(/ /,'<br />') + "</td>";
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
                // Pull the id out of the URL
                var id = url.replace(/^\//, '').split('/')[3];
                $state.go('inventorySyncStdout', {id: id});

            };

            $scope.editInventory = function (id) {
                $state.go('inventories.edit', {inventory_id: id});
            };

            $scope.manageInventory = function(id){
              $location.path($location.path() + '/' + id + '/manage');
            };

            // Failed jobs link. Go to the jobs tabs, find all jobs for the inventory and sort by status
            $scope.viewJobs = function (id) {
                $location.url('/jobs/?inventory__int=' + id);
            };

            $scope.viewFailedJobs = function (id) {
                $location.url('/jobs/?inventory__int=' + id + '&status=failed');
            };

            $scope.formCancel = function(){
                $scope.$parent.activeCard = null;
                $state.go('organizations');
            };

    }
];
