/************************************
 * Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *
 *  Jobs.js
 *  
 *  Controller functions for the Job model.
 *
 */

'use strict';

function JobsList ($scope, $rootScope, $location, $log, $routeParams, Rest, Alert, JobList,
                           GenerateList, LoadBreadCrumbs, Prompt, SearchInit, PaginateInit, ReturnToCaller,
                           ClearScope, ProcessErrors, GetBasePath, LookUpInit)
{
    ClearScope('htmlTemplate');
    var list = JobList;
    var defaultUrl = GetBasePath('jobs');
    var view = GenerateList;
    var base = $location.path().replace(/^\//,'').split('/')[0];
    var scope = view.inject(list, { mode: 'edit' });
    scope.selected = [];
  
    SearchInit({ scope: scope, set: 'jobs', list: list, url: defaultUrl });
    PaginateInit({ scope: scope, list: list, url: defaultUrl });
    scope.search(list.iterator);

    LoadBreadCrumbs();
  
}

JobsList.$inject = [ '$scope', '$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'JobList',
                     'GenerateList', 'LoadBreadCrumbs', 'Prompt', 'SearchInit', 'PaginateInit', 'ReturnToCaller', 'ClearScope',
                     'ProcessErrors','GetBasePath', 'LookUpInit'
                     ];