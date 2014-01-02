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
    GetBasePath, SearchInit, PaginateInit, FormatDate, HostsStatusMsg, UpdateStatusMsg, ViewUpdateStatus, Stream) {

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
        var msg, update_status, last_update;
        for (var i=0; i < scope.home_groups.length; i++) {
            
            scope['home_groups'][i]['inventory_name'] = scope['home_groups'][i]['summary_fields']['inventory']['name'];

            last_update = (scope.home_groups[i].summary_fields.inventory_source.last_updated == null) ? null : 
                FormatDate(new Date(scope.home_groups[i].summary_fields.inventory_source.last_updated));    
             
            // Set values for Failed Hosts column
            scope.home_groups[i].failed_hosts = scope.home_groups[i].hosts_with_active_failures + ' / ' + scope.home_groups[i].total_hosts;
            
            msg = HostsStatusMsg({
                active_failures: scope.home_groups[i].hosts_with_active_failures,
                total_hosts: scope.home_groups[i].total_hosts,
                inventory_id: scope.home_groups[i].inventory,
                group_id: scope.home_groups[i].id
                });
            
            update_status = UpdateStatusMsg({ status: scope.home_groups[i].summary_fields.inventory_source.status });

            scope.home_groups[i].failed_hosts_tip = msg['tooltip']; 
            scope.home_groups[i].failed_hosts_link = msg['url'];
            scope.home_groups[i].failed_hosts_class = msg['class'];
            scope.home_groups[i].status = update_status['status'];
            scope.home_groups[i].source = scope.groups[i].summary_fields.inventory_source.source;
            scope.home_groups[i].last_updated = last_update;
            scope.home_groups[i].status_badge_class = update_status['class'];
            scope.home_groups[i].status_badge_tooltip = update_status['tooltip'];
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
    scope.viewUpdateStatus = function(id) { ViewUpdateStatus({ scope: scope, group_id: id }) };

    }

HomeGroups.$inject = [ '$location', '$routeParams', 'HomeGroupList', 'GenerateList', 'ProcessErrors', 'LoadBreadCrumbs', 'ReturnToCaller', 
    'ClearScope', 'GetBasePath', 'SearchInit', 'PaginateInit', 'FormatDate', 'HostsStatusMsg', 'UpdateStatusMsg', 'ViewUpdateStatus', 'Stream'
    ];


function HomeHosts ($location, $routeParams, HomeHostList, GenerateList, ProcessErrors, LoadBreadCrumbs, ReturnToCaller, ClearScope, 
    GetBasePath, SearchInit, PaginateInit, FormatDate, SetHostStatus, ToggleHostEnabled, HostsEdit, Stream) {

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
            SetHostStatus(scope['hosts'][i]);
        }
        });

    SearchInit({ scope: scope, set: 'hosts', list: list, url: defaultUrl });
    PaginateInit({ scope: scope, list: list, url: defaultUrl });
    
    // Process search params
    if ($routeParams['name']) {
        scope[HomeHostList.iterator + 'InputDisable'] = false;
        scope[HomeHostListiterator + 'SearchValue'] = $routeParams['name'];
        scope[HomeHostList.iterator + 'SearchField'] = 'name';
        scope[lHomeHostList.iterator + 'SearchFieldLabel'] = list.fields['name'].label;
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
    scope.toggle_host_enabled = function(id, sources) { ToggleHostEnabled(id, sources, scope); }

    scope.editHost = function(host_id, host_name) {
        var host;
        for (var i=0; i < scope['hosts'].length; i++) {
            if (scope['hosts'][i].id == host_id) {
               host = scope['hosts'][i];
               break;
            }
        }
        if (host) {
           HostsEdit({ host_id: host_id, inventory_id: host.inventory, group_id: null, hostsReload: false });
        }
        }

    }

HomeHosts.$inject = [ '$location', '$routeParams', 'HomeHostList', 'GenerateList', 'ProcessErrors', 'LoadBreadCrumbs', 'ReturnToCaller', 
    'ClearScope', 'GetBasePath', 'SearchInit', 'PaginateInit', 'FormatDate', 'SetHostStatus', 'ToggleHostEnabled', 'HostsEdit', 'Stream'
    ]; 
