/************************************
 * Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *
 *  Jobs.js
 *
 *  Controller functions for the Inventory model.
 *
 */
 
'use strict';

function JobsList($scope, $compile, ClearScope, Breadcrumbs, LoadScope, JobList) {
    
    ClearScope();

    var e, completed_scope, running_scope, queued_scope, schedule_scope,
        completed_list, running_list, queued_list, schedule_list;

    // Add breadcrumbs
    e = angular.element(document.getElementById('breadcrumbs'));
    e.html(Breadcrumbs({ list: JobList, mode: 'edit' }));
    $compile(e)($scope);

    completed_list = angular.copy(JobList);
    completed_list.name = "completed_jobs";
    completed_list.iterator = "completed_jobs";
    completed_list.editTitle = "Completed";
    completed_scope = $scope.$new();
    LoadScope({
        scope: completed_scope,
        list: completed_list,
        id: 'completed_jobs',
        url: '/api/v1/jobs'
    });

    running_list = angular.copy(JobList);
    running_list.name   = "running_jobs";
    running_list.iterator = "running_job";
    running_list.editTitle = "Running";
    running_scope = $scope.$new();
    LoadScope({
        scope: running_scope,
        list: running_list,
        id: 'running_jobs',
        url: '/api/v1/jobs'
    });

}

JobsList.$inject = ['$scope', '$compile', 'ClearScope', 'Breadcrumbs', 'LoadScope', 'JobList'];



