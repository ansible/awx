/************************************
 * Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *
 *  JobHosts.js
 *  
 *  Controller functions for the Job Hosts Summary model.
 *
 */

'use strict';

function JobHostSummaryList ($scope, $rootScope, $location, $log, $routeParams, Rest, Alert, JobHostList,
                             GenerateList, LoadBreadCrumbs, Prompt, SearchInit, PaginateInit, ReturnToCaller,
                             ClearScope, ProcessErrors, GetBasePath)
{
    ClearScope('htmlTemplate');
    var list = JobHostList;
    var defaultUrl = GetBasePath('jobs') + $routeParams.id + '/job_host_summaries/';
    var view = GenerateList;
    var base = $location.path().replace(/^\//,'').split('/')[0];
    var scope = view.inject(list, { mode: 'edit' });
    scope.selected = [];
    
    // After a refresh, populate any needed summary field values on each row
    if (scope.PostRefreshRemove) {
       scope.PostRefreshRemove();
    }
    scope.PostRefershRemove = scope.$on('PostRefresh', function() {
        for( var i=0; i < scope.jobhosts.length; i++) {
           scope.jobhosts[i].host_name = scope.jobhosts[i].summary_fields.host.name; 
        }     
        });
  
    SearchInit({ scope: scope, set: 'jobhosts', list: list, url: defaultUrl });
    PaginateInit({ scope: scope, list: list, url: defaultUrl });
    scope.search(list.iterator);

    LoadBreadCrumbs();

    scope.viewHost = function(id) {
        Rest.setUrl(GetBasePath('jobs') + $routeParams.id + '/'); 
        Rest.get()
            .success( function(data, status, headers, config) {
                LoadBreadCrumbs({ path: '/inventories/' + data.inventory, title: data.summary_fields.inventory.name });
                $location.path('/inventories/' + data.inventory + /hosts/ + id);
                })
            .error( function(data, status, headers, config) {
                ProcessErrors(scope, data, status, null,
                   { hdr: 'Error!', msg: 'Failed to lookup job record for job ' + $routeParams.id + ' GET returned status: ' + status });
                });
        };

    scope.refresh = function() {
       scope.search(list.iterator);
       }

    scope.jobDetails = function() {
       $location.path('/jobs/' + $routeParams.id);
       };

    scope.jobEvents = function() {
       $location.path('/jobs/' + $routeParams.id + '/job_events');
       };
  
}

JobHostSummaryList.$inject = [ '$scope', '$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'JobHostList',
                               'GenerateList', 'LoadBreadCrumbs', 'Prompt', 'SearchInit', 'PaginateInit', 'ReturnToCaller', 'ClearScope',
                               'ProcessErrors','GetBasePath'
                               ];
