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

function Home ($scope, $compile, $routeParams, $rootScope, $location, Wait, ObjectCount, JobStatus, InventorySyncStatus, SCMSyncStatus, 
    ClearScope, Stream, Rest, GetBasePath, ProcessErrors, Button) {
    
    ClearScope('home');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                         //scope.
    
    //var element = angular.element(document.getElementById('htmlTemplate'));
    //var scope = element.scope();

    // Add buttons to the top of the Home page. We're using lib/ansible/generator_helpers.js-> Buttons()
    // to build buttons dynamically and insure all styling and icons match the rest of the application.
    var buttons = {
        refresh: {
            mode: 'all',
            awToolTip: "Refresh the page",
            ngClick: "refresh()"
            },
        stream: {
            ngClick: "showActivity()",
            awToolTip: "View Activity Stream",
            mode: 'all',
            ngShow: "user_is_superuser"
            }
        };
    var html = Button({ btn: buttons.refresh, action: 'refresh', toolbar: true });
    html += Button({ btn: buttons.stream, action: 'stream', toolbar: true });
    var e = angular.element(document.getElementById('home-list-actions'));
    e.html(html);
    $compile(e)($scope);

    var waitCount = 4;
    var loadedCount = 0;
        
    if (!$routeParams['login']) {
        // If we're not logging in, start the Wait widget. Otherwise, it's already running.
        Wait('start');
    }

    if ($scope.removeWidgetLoaded) {
        $scope.removeWidgetLoaded();
    }
    $scope.removeWidgetLoaded = $scope.$on('WidgetLoaded', function() {
        // Once all the widgets report back 'loaded', turn off Wait widget
        loadedCount++; 
        if ( loadedCount == waitCount ) {
            Wait('stop');
        }
        });

    if ($scope.removeDashboardReady) {
        $scope.removeDashboardReady();
    }
    $scope.removeDashboardReady = $scope.$on('dashboardReady', function(e, data) {
        JobStatus({ scope: $scope, target: 'container1', dashboard: data});
        InventorySyncStatus({ scope: $scope, target: 'container2', dashboard: data});
        SCMSyncStatus({ scope: $scope, target: 'container4', dashboard: data});
        ObjectCount({ scope: $scope, target: 'container3', dashboard: data});
        });
    
    $scope.showActivity = function() { Stream(); } 

    $scope.refresh = function() {
        Wait('start');
        loadedCount = 0;
        Rest.setUrl(GetBasePath('dashboard'));
        Rest.get()
            .success( function(data, status, headers, config) {
                $scope.$emit('dashboardReady', data);
            })
            .error ( function(data, status, headers, config) {
                Wait('stop');
                ProcessErrors($scope, data, status, null,
                    { hdr: 'Error!', msg: 'Failed to get dashboard: ' + status });
            })
        }
    
    $scope.refresh();
    
    }

Home.$inject=['$scope', '$compile', '$routeParams', '$rootScope', '$location', 'Wait', 'ObjectCount', 'JobStatus', 'InventorySyncStatus',
    'SCMSyncStatus', 'ClearScope', 'Stream', 'Rest', 'GetBasePath', 'ProcessErrors', 'Button'];


function HomeGroups ($location, $routeParams, HomeGroupList, GenerateList, ProcessErrors, LoadBreadCrumbs, ReturnToCaller, ClearScope, 
    GetBasePath, SearchInit, PaginateInit, FormatDate, GetHostsStatusMsg, GetSyncStatusMsg, ViewUpdateStatus, Stream, GroupsEdit, Wait,
    Alert, Rest, Empty, InventoryUpdate, Find) {

    ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                 //scope.

    var generator = GenerateList;
    var list = HomeGroupList;
    var defaultUrl=GetBasePath('groups');

    var scope = generator.inject(list, { mode: 'edit' });
    var base = $location.path().replace(/^\//,'').split('/')[0];

    if (scope.removePostRefresh) {
        scope.removePostRefresh();
    }
    scope.removePostRefresh = scope.$on('PostRefresh', function() {
        var hosts_status, update_status, last_update, stat;
        for (var i=0; i < scope.home_groups.length; i++) {
            
            scope['home_groups'][i]['inventory_name'] = scope['home_groups'][i]['summary_fields']['inventory']['name'];

            stat = GetSyncStatusMsg({ 
                status: scope.home_groups[i].summary_fields.inventory_source.status
                });   // from helpers/Groups.js
    
            hosts_status = GetHostsStatusMsg({
                active_failures: scope.home_groups[i].hosts_with_active_failures,
                total_hosts: scope.home_groups[i].total_hosts,
                inventory_id: scope.home_groups[i].inventory,
                group_id: scope.home_groups[i].id
                });
 
            scope['home_groups'][i].status_class = stat['class'],
            scope['home_groups'][i].status_tooltip = stat['tooltip'],
            scope['home_groups'][i].launch_tooltip = stat['launch_tip'],
            scope['home_groups'][i].launch_class = stat['launch_class'],
            scope['home_groups'][i].hosts_status_tip = hosts_status['tooltip'],
            scope['home_groups'][i].show_failures = hosts_status['failures'],
            scope['home_groups'][i].hosts_status_class = hosts_status['class'],
            
            //scope.home_groups[i].failed_hosts_tip = msg['tooltip']; 
            //scope.home_groups[i].failed_hosts_link = msg['url'];
            //scope.home_groups[i].failed_hosts_class = msg['class'];
            scope.home_groups[i].status = scope.home_groups[i].summary_fields.inventory_source.status;
            scope.home_groups[i].source = (scope.home_groups[i].summary_fields.inventory_source) ? 
                scope.home_groups[i].summary_fields.inventory_source.source : null;
            //scope.home_groups[i].last_updated = last_update;
            //scope.home_groups[i].status_badge_class = update_status['class'];
            //scope.home_groups[i].status_badge_tooltip = update_status['tooltip'];
        }
        });

    SearchInit({ scope: scope, set: 'home_groups', list: list, url: defaultUrl });
    PaginateInit({ scope: scope, list: list, url: defaultUrl });

    // Process search params
    if ($routeParams['name']) {
        scope[list.iterator + 'InputDisable'] = false;
        scope[list.iterator + 'SearchValue'] = $routeParams['name'];
        scope[list.iterator + 'SearchField'] = 'name';
        scope[list.iterator + 'SearchFieldLabel'] = list.fields['name'].label;
        scope[list.iterator + 'SearchSelectValue'] = null;
    }

    if ($routeParams['id']) {
        scope[list.iterator + 'InputDisable'] = false;
        scope[list.iterator + 'SearchValue'] = $routeParams['id'];
        scope[list.iterator + 'SearchField'] = 'id';
        scope[list.iterator + 'SearchFieldLabel'] = list.fields['id'].label;
        scope[list.iterator + 'SearchSelectValue'] = null;
    }

    if ($routeParams['has_active_failures']) {
        scope[list.iterator + 'InputDisable'] = true;
        scope[list.iterator + 'SearchValue'] = $routeParams['has_active_failures'];
        scope[list.iterator + 'SearchField'] = 'has_active_failures';
        scope[list.iterator + 'SearchFieldLabel'] = list.fields['has_active_failures'].label;
        scope[list.iterator + 'SearchSelectValue'] = ($routeParams['has_active_failures'] == 'true') ? { value: 1 } : { value: 0 };
    }

    if ($routeParams['status'] && !$routeParams['source']) {
        scope[list.iterator + 'SearchField'] = 'status';
        scope[list.iterator + 'SelectShow'] = true;
        scope[list.iterator + 'SearchSelectOpts'] = list.fields['status'].searchOptions;
        scope[list.iterator + 'SearchFieldLabel'] = list.fields['status'].label.replace(/\<br\>/g,' ');
        for (var opt in list.fields['status'].searchOptions) {
           if (list.fields['status'].searchOptions[opt].value == $routeParams['status']) {
              scope[list.iterator + 'SearchSelectValue'] = list.fields['status'].searchOptions[opt];
              break;
           }
        }
    }

    if ($routeParams['source']) {
        scope[list.iterator + 'SearchField'] = 'source';
        scope[list.iterator + 'SelectShow'] = true;
        scope[list.iterator + 'SearchSelectOpts'] = list.fields['source'].searchOptions;
        scope[list.iterator + 'SearchFieldLabel'] = list.fields['source'].label.replace(/\<br\>/g,' ');
        for (var opt in list.fields['source'].searchOptions) {
           if (list.fields['source'].searchOptions[opt].value == $routeParams['source']) {
              scope[list.iterator + 'SearchSelectValue'] = list.fields['source'].searchOptions[opt];
              break;
           }
        }

        if ($routeParams['status']) {
           scope[list.iterator + 'ExtraParms'] = '&inventory_source__status__icontains=' + $routeParams['status'];
        }
    }

    if ($routeParams['has_external_source']) {
        scope[list.iterator + 'SearchField'] = 'has_external_source';
        scope[list.iterator + 'SearchValue'] = list.fields['has_external_source'].searchValue; 
        scope[list.iterator + 'InputDisable'] = true;
        scope[list.iterator + 'SearchType'] = 'in';
        scope[list.iterator + 'SearchFieldLabel'] = list.fields['has_external_source'].label;
    }
    
    scope.search(list.iterator);
   
    LoadBreadCrumbs();
    
    scope.showActivity = function() { Stream(); }

    scope.editGroup = function(group_id, inventory_id) { 
        GroupsEdit({ scope: scope, group_id: group_id, inventory_id: inventory_id, groups_reload: false });
        }
    
    scope.viewUpdateStatus = function(id) { 
        scope.groups = scope.home_groups;
        ViewUpdateStatus({ scope: scope, tree_id: id }) 
        };

    // Launch inventory sync
    scope.updateGroup = function(id) {
        var group = Find({ list: scope.home_groups, key: 'id', val: id});
        if (group) {
            if (Empty(group.source)) {
                // if no source, do nothing. 
            }
            else if (group.status == 'updating') {
                Alert('Update in Progress', 'The inventory update process is currently running for group <em>' +
                    scope.home_groups[i].name + '</em>. Use the Refresh button to monitor the status.', 'alert-info'); 
            }
            else {
                Wait('start');
                Rest.setUrl(group.related.inventory_source);
                Rest.get()
                    .success( function(data, status, headers, config) {
                        InventoryUpdate({
                            scope: scope, 
                            url: data.related.update,
                            group_name: data.summary_fields.group.name, 
                            group_source: data.source,
                            tree_id: group.id,
                            group_id: group.id
                            });
                        })
                    .error( function(data, status, headers, config) {
                        ProcessErrors(scope, data, status, form,
                            { hdr: 'Error!', msg: 'Failed to retrieve inventory source: ' + group.related.inventory_source + 
                            ' POST returned status: ' + status });
                        });
            }
        }      
        }

    scope.refresh = function() { scope.search(list.iterator, null, false, true); }

    }

HomeGroups.$inject = [ '$location', '$routeParams', 'HomeGroupList', 'GenerateList', 'ProcessErrors', 'LoadBreadCrumbs', 'ReturnToCaller', 
    'ClearScope', 'GetBasePath', 'SearchInit', 'PaginateInit', 'FormatDate', 'GetHostsStatusMsg', 'GetSyncStatusMsg', 'ViewUpdateStatus',
    'Stream', 'GroupsEdit', 'Wait', 'Alert', 'Rest', 'Empty', 'InventoryUpdate', 'Find'
    ];


function HomeHosts ($location, $routeParams, HomeHostList, GenerateList, ProcessErrors, LoadBreadCrumbs, ReturnToCaller, ClearScope, 
    GetBasePath, SearchInit, PaginateInit, FormatDate, SetStatus, ToggleHostEnabled, HostsEdit, Stream, Find, ShowJobSummary) {

    ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                 //scope.

    var generator = GenerateList;
    var list = HomeHostList;
    var defaultUrl=GetBasePath('hosts');

    var scope = generator.inject(list, { mode: 'edit' });
    var base = $location.path().replace(/^\//,'').split('/')[0];

    if (scope.removePostRefresh) {
       scope.removePostRefresh();
    }
    scope.removePostRefresh = scope.$on('PostRefresh', function() {
        for (var i=0; i < scope.hosts.length; i++) {
            scope['hosts'][i]['inventory_name'] = scope['hosts'][i]['summary_fields']['inventory']['name'];
            //SetHostStatus(scope['hosts'][i]);
            SetStatus({ scope: scope, host: scope['hosts'][i] });
        }
        });

    SearchInit({ scope: scope, set: 'hosts', list: list, url: defaultUrl });
    PaginateInit({ scope: scope, list: list, url: defaultUrl });
    
    // Process search params
    if ($routeParams['name']) {
        scope[HomeHostList.iterator + 'InputDisable'] = false;
        scope[HomeHostList.iterator + 'SearchValue'] = $routeParams['name'];
        scope[HomeHostList.iterator + 'SearchField'] = 'name';
        scope[HomeHostList.iterator + 'SearchFieldLabel'] = list.fields['name'].label;
    }
    
    if ($routeParams['id']) {
        scope[HomeHostList.iterator + 'InputDisable'] = false;
        scope[HomeHostList.iterator + 'SearchValue'] = $routeParams['id'];
        scope[HomeHostList.iterator + 'SearchField'] = 'id';
        scope[HomeHostList.iterator + 'SearchFieldLabel'] = list.fields['id'].label;
        scope[HomeHostList.iterator + 'SearchSelectValue'] = null;
    }

    if ($routeParams['has_active_failures']) {
        scope[HomeHostList.iterator + 'InputDisable'] = true;
        scope[HomeHostList.iterator + 'SearchValue'] = $routeParams['has_active_failures'];
        scope[HomeHostList.iterator + 'SearchField'] = 'has_active_failures';
        scope[HomeHostList.iterator + 'SearchFieldLabel'] = HomeHostList.fields['has_active_failures'].label;
        scope[HomeHostList.iterator + 'SearchSelectValue'] = ($routeParams['has_active_failures'] == 'true') ? { value: 1 } : { value: 0 };
    }
    
    scope.search(list.iterator);
   
    LoadBreadCrumbs();
    
    scope.showActivity = function() { Stream(); }

    scope.toggle_host_enabled = function(id, sources) { ToggleHostEnabled({ host_id: id, external_source: sources, scope: scope }); }

    scope.editHost = function(host_id, host_name) {
        var host = Find({ list: scope.hosts, key: 'id', val: host_id });
        if (host) {
            HostsEdit({ scope: scope, host_id: host_id, inventory_id: host.inventory, group_id: null, hostsReload: false });
        }
        }

    scope.showJobSummary = function(job_id) { 
        ShowJobSummary({ job_id: job_id });
        }

    }

HomeHosts.$inject = [ '$location', '$routeParams', 'HomeHostList', 'GenerateList', 'ProcessErrors', 'LoadBreadCrumbs', 'ReturnToCaller', 
    'ClearScope', 'GetBasePath', 'SearchInit', 'PaginateInit', 'FormatDate', 'SetStatus', 'ToggleHostEnabled', 'HostsEdit', 'Stream',
    'Find', 'ShowJobSummary'
    ]; 
