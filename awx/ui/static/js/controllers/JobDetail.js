/************************************
 * Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  JobDetail.js
 *
 */
 
'use strict';

function JobDetailController ($scope, $compile, $routeParams, ClearScope, Breadcrumbs, LoadBreadCrumbs, GetBasePath, Wait, Rest, ProcessErrors, DigestEvents) {
    
    ClearScope();

    var job_id = $routeParams.id,
        job;

    /*LoadBreadCrumbs();

    e = angular.element(document.getElementById('breadcrumbs'));
    e.html(Breadcrumbs({ list: { editTitle: 'Jobs' } , mode: 'edit' }));
    $compile(e)($scope);
    */

    $scope.plays = [];
    $scope.tasks = [];

    // Apply each event to the view
    if ($scope.removeEventsReady) {
        $scope.removeEventsReady();
    }
    $scope.removeEventsReady = $scope.$on('EventsReady', function(e, events) {
        DigestEvents({
            scope: $scope,
            events: events
        });
    });
    
    // Get events, page size 50
    if ($scope.removeJobReady) {
        $scope.removeJobReady();
    }
    $scope.removeJobReady = $scope.$on('JobReady', function(e, next) {
        if (next) {
            Rest.setUrl(next);
            Rest.get()
                .success(function(data) {
                    $scope.$emit('EventsReady', data.results);
                    if (data.next) {
                        $scope.$emit('JobReady', data.next);
                    }
                })
                .error(function(data, status) {
                    ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                        msg: 'Failed to retrieve job events: ' + next + ' GET returned: ' + status });
                });
        }
    });

    // Load the job record
    Rest.setUrl(GetBasePath('jobs') + job_id + '/');
    Rest.get()
        .success(function(data) {
            job = data;
            $scope.job_template_name = data.name;
            $scope.project_name = (data.summary_fields.project) ? data.summary_fields.project.name : '';
            $scope.inventory_name = (data.summary_fields.inventory) ? data.summary_fields.inventory.name : '';
            $scope.job_template_url = '/#/job_templates/' + data.unified_job_template;
            $scope.inventory_url = ($scope.inventory_name && data.inventory) ? '/#/inventories/' + data.inventory : '';
            $scope.project_url = ($scope.project_name && data.project) ? '/#/projects/' + data.project : '';
            $scope.job_type = data.job_type;
            $scope.playbook = data.playbook;
            $scope.credential = data.credential;
            $scope.cloud_credential = data.cloud_credential;
            $scope.forks = data.forks;
            $scope.limit = data.limit;
            $scope.verbosity = data.verbosity;
            $scope.job_tags = data.job_tags;
            $scope.$emit('JobReady', data.related.job_events + '?page_size=50&order_by=id');
        })
        .error(function(data, status) {
            ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                msg: 'Failed to retrieve job: ' + $routeParams.id + '. GET returned: ' + status });
        });
}

JobDetailController.$inject = [ '$scope', '$compile', '$routeParams', 'ClearScope', 'Breadcrumbs', 'LoadBreadCrumbs', 'GetBasePath', 'Wait',
    'Rest', 'ProcessErrors', 'DigestEvents'
];
