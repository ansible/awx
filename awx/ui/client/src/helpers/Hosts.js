/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


/* jshint loopfunc: true */
/**
 * @ngdoc function
 * @name helpers.function:Hosts
 * @description    Routines that handle host add/edit/delete on the Inventory detail page.
 */

'use strict';

import listGenerator from '../shared/list-generator/main';

export default
angular.module('HostsHelper', [ 'RestServices', 'Utilities', listGenerator.name, 'HostListDefinition',
               'SearchHelper', 'PaginationHelpers', listGenerator.name, 'HostsHelper',
               'InventoryHelper', 'RelatedSearchHelper', 'InventoryFormDefinition', 'SelectionHelper',
               'HostGroupsFormDefinition', 'VariablesHelper', 'ModalDialog', 'StandardOutHelper',
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

                        html += "<td>" + ($filter('longDate')(job.finished)).replace(/ /,'<br />') + "</td>\n";

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

.factory('HostsReload', [ '$stateParams', 'Empty', 'InventoryHosts', 'GetBasePath', 'SearchInit', 'PaginateInit', 'Wait',
         'SetHostStatus', 'SetStatus', 'ApplyEllipsis',
         function($stateParams, Empty, InventoryHosts, GetBasePath, SearchInit, PaginateInit, Wait, SetHostStatus, SetStatus,
                  ApplyEllipsis) {
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

                          SearchInit({ scope: scope, set: 'hosts', list: list, url: url });
                          PaginateInit({ scope: scope, list: list, url: url, pageSize: pageSize });

                          if ($stateParams.host_name) {
                              scope[list.iterator + 'InputDisable'] = false;
                              scope[list.iterator + 'SearchValue'] = $stateParams.host_name;
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

.factory('HostsCopy', ['$compile', 'Rest', 'ProcessErrors', 'CreateDialog', 'GetBasePath', 'Wait', 'generateList', 'GroupList', 'SearchInit',
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
                if (row.checked) {
                    scope[list.name][i].success_class = 'success';
                }
                else {
                    scope[list.name][i].success_class = '';
                }
            } else {
                scope[list.name][i].checked = 0;
                scope[list.name][i].success_class = '';
            }
        });
        // Check if any rows are checked
        scope[list.name].forEach(function(row) {
            if (row.checked) {
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
                if (row.checked === 1) {
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
}]);