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

function JobsList($scope, $compile, ClearScope, Breadcrumbs, LoadScope, RunningJobsList, CompletedJobsList, QueuedJobsList,
    GetChoices, GetBasePath, Wait) {
    
    ClearScope();

    var e, completed_scope, running_scope, queued_scope, choicesCount = 0, listsCount = 0;
    // schedule_scope;

    // Add breadcrumbs
    e = angular.element(document.getElementById('breadcrumbs'));
    e.html(Breadcrumbs({ list: { editTitle: 'Jobs' } , mode: 'edit' }));
    $compile(e)($scope);

    // After all the lists are loaded
    if ($scope.removeListLoaded) {
        $scope.removeListLoaded();
    }
    $scope.removeListLoaded = $scope.$on('listLoaded', function() {
        listsCount++;
        if (listsCount === 3) {
            Wait('stop');
        }
    });
    
    // After all choices are ready, load up the lists and populate the page
    if ($scope.removeBuildJobsList) {
        $scope.removeBuildJobsList();
    }
    $scope.removeBuildJobsList = $scope.$on('buildJobsList', function() {
        completed_scope = $scope.$new();
        LoadScope({
            parent_scope: $scope,
            scope: completed_scope,
            list: CompletedJobsList,
            id: 'completed-jobs',
            url: '/static/sample/data/jobs/completed/data.json'
        });
        running_scope = $scope.$new();
        LoadScope({
            parent_scope: $scope,
            scope: running_scope,
            list: RunningJobsList,
            id: 'active-jobs',
            url: '/static/sample/data/jobs/running/data.json'
        });
        queued_scope = $scope.$new();
        LoadScope({
            parent_scope: $scope,
            scope: queued_scope,
            list: QueuedJobsList,
            id: 'queued-jobs',
            url: '/static/sample/data/jobs/queued/data.json'
        });
    });

    if ($scope.removeChoicesReady) {
        $scope.removeChoicesReady();
    }
    $scope.removeChoicesReady = $scope.$on('choicesReady', function() {
        choicesCount++;
        if (choicesCount === 2) {
            $scope.$emit('buildJobsList');
        }
    });

    Wait('start');

    GetChoices({
        scope: $scope,
        url: GetBasePath('jobs'),
        field: 'status',
        variable: 'status_choices',
        callback: 'choicesReady'
    });
    
    /* Use for types later 
    GetChoices({
        scope: $scope,
        url: GetBasePath('jobs'),
        field: 'type',
        variable: 'types',
        callback: ''
    });
    */

    $scope.type_choices = [{
        label: 'Inventory sync',
        value: 'inventory_sync',
        name: 'inventory_sync'
    },{
        label: 'Project sync',
        value: 'scm_sync',
        name: 'scm_sync'
    },{
        label: 'Playbook run',
        value: 'playbook_run',
        name: 'playbook_run'
    }];
    $scope.$emit('choicesReady');
}

JobsList.$inject = ['$scope', '$compile', 'ClearScope', 'Breadcrumbs', 'LoadScope', 'RunningJobsList', 'CompletedJobsList',
    'QueuedJobsList', 'GetChoices', 'GetBasePath', 'Wait'];



