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

function JobsList($scope, $compile, ClearScope, Breadcrumbs, LoadScope, RunningJobsList, CompletedJobsList, QueuedJobsList) {
    
    ClearScope();

    var e, completed_scope, running_scope, queued_scope, schedule_scope;

    // Add breadcrumbs
    e = angular.element(document.getElementById('breadcrumbs'));
    e.html(Breadcrumbs({ list: { editTitle: 'Jobs' } , mode: 'edit' }));
    $compile(e)($scope);

    completed_scope = $scope.$new();
    LoadScope({
        scope: completed_scope,
        list: CompletedJobsList,
        id: 'completed-jobs',
        url: '/static/sample/data/jobs/completed/data.json'
    });

    running_scope = $scope.$new();
    LoadScope({
        scope: running_scope,
        list: RunningJobsList,
        id: 'active-jobs',
        url: '/static/sample/data/jobs/running/data.json'
    });

    queued_scope = $scope.$new();
    LoadScope({
        scope: queued_scope,
        list: QueuedJobsList,
        id: 'queued-jobs',
        url: '/static/sample/data/jobs/queued/data.json'
    });

}

JobsList.$inject = ['$scope', '$compile', 'ClearScope', 'Breadcrumbs', 'LoadScope', 'RunningJobsList', 'CompletedJobsList', 'QueuedJobsList'];



