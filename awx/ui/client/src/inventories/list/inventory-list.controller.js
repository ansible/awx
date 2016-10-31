/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/**
 * @ngdoc function
 * @name controllers.function:Inventories
 * @description This controller's for the Inventory page
 */

function InventoriesList($scope, $rootScope, $location, $log,
    $stateParams, $compile, $filter, sanitizeFilter, Rest, Alert, InventoryList, Prompt,
    ClearScope, ProcessErrors, GetBasePath, Wait, Find, Empty, $state, rbacUiControlService, Dataset) {

    let list = InventoryList,
        defaultUrl = GetBasePath('inventory');

    init();

    function init(){
        $scope.canAdd = false;

        rbacUiControlService.canAdd('inventory')
            .then(function(canAdd) {
                $scope.canAdd = canAdd;
            });

        $scope.$watchCollection(list.name, function(){
            _.forEach($scope[list.name], buildStatusIndicators);
        });

        // Search init
        $scope.list = list;
        $scope[`${list.iterator}_dataset`] = Dataset.data;
        $scope[list.name] = $scope[`${list.iterator}_dataset`].results;

        $rootScope.flashMessage = null;

    }

    function buildStatusIndicators(inventory){
            inventory.launch_class = "";
            if (inventory.has_inventory_sources) {
                if (inventory.inventory_sources_with_failures > 0) {
                    inventory.syncStatus = 'error';
                    inventory.syncTip = inventory.inventory_sources_with_failures + ' groups with sync failures. Click for details';
                }
                else {
                    inventory.syncStatus = 'successful';
                    inventory.syncTip = 'No inventory sync failures. Click for details.';
                }
            }
            else {
                inventory.syncStatus = 'na';
                inventory.syncTip = 'Not configured for inventory sync.';
                inventory.launch_class = "btn-disabled";
            }
            if (inventory.has_active_failures) {
                inventory.hostsStatus = 'error';
                inventory.hostsTip = inventory.hosts_with_active_failures + ' hosts with failures. Click for details.';
            }
            else if (inventory.total_hosts) {
                inventory.hostsStatus = 'successful';
                inventory.hostsTip = 'No hosts with failures. Click for details.';
            }
            else {
                inventory.hostsStatus = 'none';
                inventory.hostsTip = 'Inventory contains 0 hosts.';
            }
    }

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
        elem.removeAttr('ng-click');
        $compile(elem)($scope);
        $scope.triggerPopover(event);
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
                html += "<td>" + ($filter('longDate')(row.finished)).replace(/ /,'<br />') + "</td>";
                html += "<td><a href=\"#/jobs/" + row.id + "\" " + "aw-tool-tip=\"" + row.status.charAt(0).toUpperCase() + row.status.slice(1) +
                    ". Click for details\" aw-tip-placement=\"top\">" + $filter('sanitize')(ellipsis(row.name)) + "</a></td>";
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
                html += `<td><a href="" ng-click="viewJob('${row.related.last_update}')" aw-tool-tip="${row.status.charAt(0).toUpperCase() + row.status.slice(1)}. Click for details" aw-tip-placement="top"><i class="SmartStatus-tooltip--${row.status} fa icon-job-${row.status}"></i></a></td>`;
                html += "<td>" + ($filter('longDate')(row.last_updated)).replace(/ /,'<br />') + "</td>";
                html += "<td><a href=\"\" ng-click=\"viewJob('" + row.related.last_update + "')\">" + $filter('sanitize')(ellipsis(row.summary_fields.group.name)) + "</a></td>";
                html += "</tr>\n";
            }
            else {
                html += "<tr>";
                html += "<td><a href=\"\" aw-tool-tip=\"No sync data\" aw-tip-placement=\"top\"><i class=\"fa icon-job-none\"></i></a></td>";
                html += "<td>NA</td>";
                html += "<td><a href=\"\">" + $filter('sanitize')(ellipsis(row.summary_fields.group.name)) + "</a></td>";
                html += "</tr>\n";
            }
        });
        html += "</tbody>\n";
        html += "</table>\n";
        title = "Sync Status";
        attachElem(event, html, title);
    });

    $scope.showGroupSummary = function(event, id) {
        try{
            var elem = $(event.target).parent();
            // if the popover is visible already, then exit the function here
            if(elem.data()['bs.popover'].tip().hasClass('in')){
                return;
            }
        }
        catch(err){
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
        }
    };

    $scope.showHostSummary = function(event, id) {
        try{
            var elem = $(event.target).parent();
            // if the popover is visible already, then exit the function here
            if(elem.data()['bs.popover'].tip().hasClass('in')){
                return;
            }
        }
        catch(err){
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
        }
    };

    $scope.viewJob = function(url) {

        // Pull the id out of the URL
        var id = url.replace(/^\//, '').split('/')[3];

        $state.go('inventorySyncStdout', {id: id});

    };

    $scope.addInventory = function () {
        $state.go('inventories.add');
    };

    $scope.editInventory = function (id) {
        $state.go('inventories.edit', {inventory_id: id});
    };

    $scope.manageInventory = function(id){
      $location.path($location.path() + '/' + id + '/manage');
    };

    $scope.deleteInventory = function (id, name) {

        var action = function () {
            var url = defaultUrl + id + '/';
            Wait('start');
            $('#prompt-modal').modal('hide');
            Rest.setUrl(url);
            Rest.destroy()
                .success(function () {
                    if (parseInt($state.params.inventory_id) === id) {
                        $state.go("^", null, {reload: true});
                    } else {
                        // @issue: OLD SEARCH
                        // $scope.search(list.iterator);
                    }
                })
                .error(function (data, status) {
                    ProcessErrors( $scope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + ' failed. DELETE returned status: ' + status
                    });
                });
        };

        Prompt({
            hdr: 'Delete',
            body: '<div class="Prompt-bodyQuery">Are you sure you want to delete the inventory below?</div><div class="Prompt-bodyTarget">' + $filter('sanitize')(name) + '</div>',
            action: action,
            actionText: 'DELETE'
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

export default ['$scope', '$rootScope', '$location', '$log',
    '$stateParams', '$compile', '$filter', 'sanitizeFilter', 'Rest', 'Alert', 'InventoryList',
    'Prompt', 'ClearScope', 'ProcessErrors', 'GetBasePath', 'Wait', 'Find', 'Empty', '$state', 'rbacUiControlService', 'Dataset', InventoriesList
];
