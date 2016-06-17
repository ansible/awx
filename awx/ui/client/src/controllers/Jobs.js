/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/**
 * @ngdoc function
 * @name controllers.function:Jobs
 * @description This controller's for the jobs page
*/


export function JobsListController ($rootScope, $log, $scope, $compile, $stateParams,
    ClearScope, LoadSchedulesScope,
    LoadJobsScope, AllJobsList, ScheduledJobsList, GetChoices, GetBasePath, Wait) {

    ClearScope();

    var jobs_scope, scheduled_scope,
        choicesCount = 0,
        listCount = 0,
        api_complete = false;

    $scope.jobsSelected = true;

    if ($scope.removeListLoaded) {
        $scope.removeListLoaded();
    }
    $scope.removeListLoaded = $scope.$on('listLoaded', function() {
        listCount++;
        if (listCount === 2) {
            api_complete = true;
        }
    });



    // After all choices are ready, load up the lists and populate the page
    if ($scope.removeBuildJobsList) {
        $scope.removeBuildJobsList();
    }
    $scope.removeBuildJobsList = $scope.$on('buildJobsList', function() {
        var opt, search_params={};

        if (AllJobsList.fields.type) {
            AllJobsList.fields.type.searchOptions = $scope.type_choices;
        }
        if ($stateParams.status) {
            search_params[AllJobsList.iterator + 'SearchField'] = 'status';
            search_params[AllJobsList.iterator + 'SelectShow'] = true;
            search_params[AllJobsList.iterator + 'SearchSelectOpts'] = AllJobsList.fields.status.searchOptions;
            search_params[AllJobsList.iterator + 'SearchFieldLabel'] = AllJobsList.fields.status.label.replace(/<br\>/g,' ');
            search_params[AllJobsList.iterator + 'SearchType'] = '';
            for (opt in AllJobsList.fields.status.searchOptions) {
                if (AllJobsList.fields.status.searchOptions[opt].value === $stateParams.status) {
                    search_params[AllJobsList.iterator + 'SearchSelectValue'] = AllJobsList.fields.status.searchOptions[opt];
                    break;
                }
            }
        }
        jobs_scope = $scope.$new(true);
        jobs_scope.showJobType = true;
        LoadJobsScope({
            parent_scope: $scope,
            scope: jobs_scope,
            list: AllJobsList,
            id: 'active-jobs',
            url: GetBasePath('unified_jobs') + '?status__in=pending,waiting,running,completed,failed,successful,error,canceled&order_by=-finished',
            searchParams: search_params,
            spinner: false
        });


        scheduled_scope = $scope.$new(true);
        LoadSchedulesScope({
            parent_scope: $scope,
            scope: scheduled_scope,
            list: ScheduledJobsList,
            id: 'scheduled-jobs-tab',
            searchSize: 'col-lg-4 col-md-4 col-sm-4 col-xs-12',
            url: GetBasePath('schedules') + '?next_run__isnull=false'
        });

        $scope.refreshJobs = function() {
            jobs_scope.search('queued_job');
            jobs_scope.search('running_job');
            jobs_scope.search('completed_job');
            scheduled_scope.search('schedule');
        };

        function clearTabs() {
           $scope.jobsSelected = false;
           $scope.schedulesSelected = false;
       }

        $scope.toggleTab = function(tab) {
           clearTabs();
           if (tab === "jobs") {
               $scope.jobsSelected = true;
           } else if (tab === "scheduled") {
               $scope.schedulesSelected = true;
           }
       };

        if ($rootScope.removeJobStatusChange) {
            $rootScope.removeJobStatusChange();
        }
        $rootScope.removeJobStatusChange = $rootScope.$on('JobStatusChange-jobs', function() {
            $scope.refreshJobs();
        });

        if ($rootScope.removeScheduleStatusChange) {
            $rootScope.removeScheduleStatusChange();
        }
        $rootScope.removeScheduleStatusChange = $rootScope.$on('ScheduleStatusChange', function() {
            if (api_complete) {
                scheduled_scope.search('schedule');
            }
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
        url: GetBasePath('unified_jobs'),
        field: 'status',
        variable: 'status_choices',
        callback: 'choicesReady'
    });

    GetChoices({
        scope: $scope,
        url: GetBasePath('unified_jobs'),
        field: 'type',
        variable: 'type_choices',
        callback: 'choicesReady'
    });
}

JobsListController.$inject = ['$rootScope', '$log', '$scope', '$compile', '$stateParams',
'ClearScope', 'LoadSchedulesScope', 'LoadJobsScope',
'AllJobsList', 'ScheduledJobsList', 'GetChoices', 'GetBasePath', 'Wait'];
