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
           scope.jobhosts[i].status = (scope.jobhosts[i].failed) ? 'error' : 'success';  
        }  
        });
  
    SearchInit({ scope: scope, set: 'jobhosts', list: list, url: defaultUrl });
    PaginateInit({ scope: scope, list: list, url: defaultUrl });

    // Called from Inventories tab, host failed events link:
    if ($routeParams.host) {
       scope[list.iterator + 'SearchField'] = 'host'; 
       scope[list.iterator + 'SearchValue'] = $routeParams.host;
       scope[list.iterator + 'SearchFieldLabel'] = list.fields['host'].label;
    }
    
    scope.search(list.iterator);

    LoadBreadCrumbs();
    
    scope.showEvents = function(host_name, last_job) {
      // When click on !Failed Events link, redirect to latest job/job_events for the host
      Rest.setUrl(last_job);
      Rest.get()
          .success( function(data, status, headers, config) {
              LoadBreadCrumbs({ path: '/jobs/' + data.id, title: data.name });
              $location.url('/jobs/' + data.id + '/job_events/?host=' + escape(host_name));
              })
          .error( function(data, status, headers, config) {
              ProcessErrors(scope, data, status, form,
                  { hdr: 'Error!', msg: 'Failed to lookup last job: ' + last_job + '. GET status: ' + status });
              });
      }

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
