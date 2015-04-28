/************************************
 * Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *
 *  Jobs.js
 *
 *  Controller functions for the Inventory model.
 *
 */
/**
 * @ngdoc function
 * @name controllers.function:Jobs
 * @description This controller's for the jobs page
*/


export function JobsListController ($rootScope, $log, $scope, $compile, $routeParams,
    ClearScope, Breadcrumbs, LoadBreadCrumbs, LoadSchedulesScope,
    LoadJobsScope, AllJobsList, ScheduledJobsList, GetChoices, GetBasePath, Wait, Socket) {

    ClearScope();

    var jobs_scope, scheduled_scope,
        choicesCount = 0,
        listCount = 0,
        api_complete = false,
        schedule_socket,
        job_socket,
        max_rows;

    function openSockets() {
        job_socket = Socket({
            scope: $scope,
            endpoint: "jobs"
        });
        job_socket.init();
        job_socket.on("status_changed", function() {
            // if (api_complete) {
                jobs_scope.refreshJobs();
            // }
        });
        schedule_socket = Socket({
            scope: $scope,
            endpoint: "schedules"
        });
        schedule_socket.init();
        schedule_socket.on("schedule_changed", function() {
            if (api_complete) {
                scheduled_scope.search('schedule');
            }
        });
    }

    LoadBreadCrumbs();

    if ($scope.removeListLoaded) {
        $scope.removeListLoaded();
    }
    $scope.removeListLoaded = $scope.$on('listLoaded', function() {
        listCount++;
        if (listCount === 2) {
            api_complete = true;
            openSockets();
        }
    });

    // After all choices are ready, load up the lists and populate the page
    if ($scope.removeBuildJobsList) {
        $scope.removeBuildJobsList();
    }
    $scope.removeBuildJobsList = $scope.$on('buildJobsList', function() {
        var opt, search_params;

        if (AllJobsList.fields.type) {
            AllJobsList.fields.type.searchOptions = $scope.type_choices;
        }
        if ($routeParams.status) {
            search_params[AllJobsList.iterator + 'SearchField'] = 'status';
            search_params[AllJobsList.iterator + 'SelectShow'] = true;
            search_params[AllJobsList.iterator + 'SearchSelectOpts'] = AllJobsList.fields.status.searchOptions;
            search_params[AllJobsList.iterator + 'SearchFieldLabel'] = AllJobsList.fields.status.label.replace(/<br\>/g,' ');
            search_params[AllJobsList.iterator + 'SearchType'] = '';
            for (opt in AllJobsList.fields.status.searchOptions) {
                if (AllJobsList.fields.status.searchOptions[opt].value === $routeParams.status) {
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
            url: GetBasePath('unified_jobs') + '?status__in=pending,running,completed,failed,successful,error,canceled',
            pageSize: max_rows,
            spinner: false
        });
        scheduled_scope = $scope.$new(true);
        LoadSchedulesScope({
            parent_scope: $scope,
            scope: scheduled_scope,
            list: ScheduledJobsList,
            id: 'scheduled-jobs-tab',
            searchSize: 'col-lg-4 col-md-4 col-sm-4 col-xs-12',
            url: GetBasePath('schedules') + '?next_run__isnull=false',
            pageSize: max_rows
        });

        $scope.refreshJobs = function() {
            jobs_scope.search('queued_job');
            jobs_scope.search('running_job');
            jobs_scope.search('completed_job');
            scheduled_scope.search('schedule');
        };

        $(window).resize(_.debounce(function() {
            resizeContainers();
        }, 500));
    });

    if ($scope.removeChoicesReady) {
        $scope.removeChoicesReady();
    }
    $scope.removeChoicesReady = $scope.$on('choicesReady', function() {
        choicesCount++;
        if (choicesCount === 2) {
            setHeight();
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

    // Set the height of each container and calc max number of rows containers can hold
    function setHeight() {
        var docw = $(window).width(),
            //doch = $(window).height(),
            available_height,
            search_row, page_row, height, header, row_height;
        $log.debug('docw: ' + docw);

        // customize the container height and # of rows based on available viewport height
        available_height = $(window).height() - $('#main-menu-container .navbar').outerHeight() - 80;
        if (docw < 1350) {
            available_height = (available_height < 800) ? 800 : available_height;
        } else {
            available_height = (available_height < 550) ? 550 : available_height;
        }
        $log.debug('available_height: ' + available_height);
        $('.jobs-list-container').each(function() {
            $(this).height(Math.floor(available_height));
        });
        search_row = Math.max($('.search-row:eq(0)').outerHeight(), 50);
        page_row = Math.max($('.page-row:eq(0)').outerHeight(), 33);
        header = Math.max($('#active_jobs_table thead').height(), 24);
        height = Math.floor(available_height ) - header - page_row - search_row - 30;
        row_height = 44;

        max_rows = Math.floor(height / row_height);
        max_rows = (max_rows < 5) ? 5 : max_rows;

        $log.debug('max_rows: ' + max_rows);
    }

    // Set container height and return the number of allowed rows
    function resizeContainers() {
        setHeight();
        jobs_scope[AllJobsList.iterator + '_page_size'] = max_rows;
        jobs_scope.changePageSize(AllJobsList.name, AllJobsList.iterator);
        scheduled_scope[ScheduledJobsList.iterator + '_page_size'] = max_rows;
        scheduled_scope.changePageSize(ScheduledJobsList.name, ScheduledJobsList.iterator);
    }
}

JobsListController.$inject = ['$rootScope', '$log', '$scope', '$compile', '$routeParams',
'ClearScope', 'Breadcrumbs', 'LoadBreadCrumbs', 'LoadSchedulesScope', 'LoadJobsScope',
'AllJobsList', 'ScheduledJobsList', 'GetChoices', 'GetBasePath', 'Wait', 'Socket'];
