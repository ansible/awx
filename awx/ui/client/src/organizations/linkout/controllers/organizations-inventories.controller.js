/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', '$rootScope', '$location',
    '$stateParams', '$compile', '$filter', 'Rest', 'InventoryList',
    'OrgInventoryDataset', 'OrgInventoryList',
    'ProcessErrors', 'GetBasePath', 'Wait', 'Find', 'Empty', '$state', 'i18n',
    function($scope, $rootScope, $location,
        $stateParams, $compile, $filter, Rest, InventoryList,
        Dataset, OrgInventoryList,
        ProcessErrors, GetBasePath, Wait,
        Find, Empty, $state, i18n) {

        var list = OrgInventoryList,
            orgBase = GetBasePath('organizations');

        init();

        function init() {
            // search init
            $scope.list = list;
            $scope[`${list.iterator}_dataset`] = Dataset.data;
            $scope[list.name] = $scope[`${list.iterator}_dataset`].results;

            $rootScope.flashMessage = null;
            Rest.setUrl(orgBase + $stateParams.organization_id);
            Rest.get()
                .then(({data}) => {

                    $scope.organization_name = data.name;
                    $scope.name = data.name;
                    $scope.org_id = data.id;
                    $scope.orgRelatedUrls = data.related;

                });

            $scope.$watch('inventories', ()=>{
                _.forEach($scope.inventories, processInventoryRow);
            });
        }

        function processInventoryRow(item) {
            if (item.has_inventory_sources) {
                if (item.inventory_sources_with_failures > 0) {
                    item.syncStatus = 'error';
                    item.syncTip = item.inventory_sources_with_failures + i18n._(' groups with sync failures. Click for details');
                } else {
                    item.syncStatus = 'successful';
                    item.syncTip = i18n._('No inventory sync failures. Click for details.');
                }
            } else {
                item.syncStatus = 'na';
                item.syncTip = i18n._('Not configured for inventory sync.');
                item.launch_class = "btn-disabled";
            }
            if (item.has_active_failures) {
                item.hostsStatus = 'eritemror';
                item.hostsTip = item.hosts_with_active_failures + i18n._(' hosts with failures. Click for details.');
            } else if (item.total_hosts) {
                item.hostsStatus = 'successful';
                item.hostsTip = i18n._('No hosts with failures. Click for details.');
            } else {
                item.hostsStatus = 'none';
                item.hostsTip = i18n._('Inventory contains 0 hosts.');
            }

            item.kind_label = item.kind === '' ? i18n._('Inventory') : (item.kind === 'smart' ? i18n._('Smart Inventory'): i18n._('Inventory'));
            item.linkToDetails = (item.kind && item.kind === 'smart') ? `inventories.editSmartInventory({smartinventory_id:${item.id}})` : `inventories.edit({inventory_id:${item.id}})`;

            return item;
        }

        function ellipsis(a) {
            if (a.length > 20) {
                return a.substr(0, 20) + '...';
            }
            return a;
        }

        function attachElem(event, html, title) {
            var elem = $(event.target).parent();
            try {
                elem.tooltip('hide');
                elem.popover('dispose');
            } catch (err) {
                //ignore
            }
            $('.popover').each(function() {
                // remove lingering popover <div>. Seems to be a bug in TB3 RC1
                $(this).remove();
            });
            $('.tooltip').each(function() {
                // close any lingering tool tipss
                $(this).hide();
            });
            elem.attr({
                "aw-pop-over": html,
                "data-popover-title": title,
                "data-placement": "right"
            });
            $compile(elem)($scope);
            elem.on('shown.bs.popover', function() {
                $('.popover').each(function() {
                    $compile($(this))($scope); //make nested directives work!
                });
                $('.popover-content, .popover-title').click(function() {
                    elem.popover('hide');
                });
            });
            elem.popover('show');
        }

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
                    html += "<td>" + ($filter('longDate')(row.finished)).replace(/ /, '<br />') + "</td>";
                    html += "<td><a href=\"#/jobs/" + row.id + "\" " + "aw-tool-tip=\"" + row.status.charAt(0).toUpperCase() + row.status.slice(1) +
                        ". Click for details\" aw-tip-placement=\"top\">" + ellipsis(row.name) + "</a></td>";
                    html += "</tr>\n";
                });
                html += "</tbody>\n";
                html += "</table>\n";
            } else {
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
            data.results.forEach(function(row) {
                if (row.related.last_update) {
                    html += "<tr>";
                    html += "<td><a href=\"\" ng-click=\"viewJob('" + row.related.last_update + "')\" aw-tool-tip=\"" + row.status.charAt(0).toUpperCase() + row.status.slice(1) + ". Click for details\" aw-tip-placement=\"top\"><i class=\"fa icon-job-" + row.status + "\"></i></a></td>";
                    html += "<td>" + ($filter('longDate')(row.last_updated)).replace(/ /, '<br />') + "</td>";
                    html += "<td><a href=\"\" ng-click=\"viewJob('" + row.related.last_update + "')\">" + ellipsis(row.summary_fields.group.name) + "</a></td>";
                    html += "</tr>\n";
                } else {
                    html += "<tr>";
                    html += "<td><a href=\"\" aw-tool-tip=\"No sync data\" aw-tip-placement=\"top\"><i class=\"fa icon-job-none\"></i></a></td>";
                    html += "<td>NA</td>";
                    html += "<td><a href=\"\">" + ellipsis(row.summary_fields.group.name) + "</a></td>";
                    html += "</tr>\n";
                }
            });
            html += "</tbody>\n";
            html += "</table>\n";
            title = i18n._("Sync Status");
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
                        .then(({data}) => {
                            $scope.$emit('GroupSummaryReady', event, inventory, data);
                        })
                        .catch(({data, status}) => {
                            ProcessErrors($scope, data, status, null, {
                                hdr: 'Error!',
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
                        .then(({data}) => {
                            $scope.$emit('HostSummaryReady', event, data);
                        })
                        .catch(({data, status}) => {
                            ProcessErrors($scope, data, status, null, {
                                hdr: 'Error!',
                                msg: 'Call to ' + url + ' failed. GET returned: ' + status
                            });
                        });
                }
            }
        };

        $scope.viewJob = function(url) {
            // Pull the id out of the URL
            var id = url.replace(/^\//, '').split('/')[3];
            $state.go('output', { id: id, type: 'inventory' });

        };

        $scope.editInventory = function (inventory) {
            if(inventory.kind && inventory.kind === 'smart') {
                $state.go('inventories.editSmartInventory', {smartinventory_id: inventory.id});
            }
            else {
                $state.go('inventories.edit', {inventory_id: inventory.id});
            }
        };

        // Failed jobs link. Go to the jobs tabs, find all jobs for the inventory and sort by status
        $scope.viewJobs = function(id) {
            $location.url('/jobs/?inventory__int=' + id);
        };

        $scope.viewFailedJobs = function(id) {
            $location.url('/jobs/?inventory__int=' + id + '&status=failed');
        };

        $scope.formCancel = function() {
            $state.go('organizations');
        };

    }
];
