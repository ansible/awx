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


export function JobsListController ($rootScope, $log, $scope, $compile, $routeParams, ClearScope, Breadcrumbs, LoadBreadCrumbs, LoadSchedulesScope,
    LoadJobsScope, RunningJobsList, CompletedJobsList, QueuedJobsList, ScheduledJobsList, GetChoices, GetBasePath, Wait, Socket) {

    ClearScope();

    var completed_scope, running_scope, queued_scope, scheduled_scope,
        choicesCount = 0,
        listCount = 0,
        api_complete = false,
        schedule_socket,
        job_socket,
        max_rows, checkCount=0;

    function openSockets() {
        job_socket = Socket({
            scope: $scope,
            endpoint: "jobs"
        });
        job_socket.init();
        job_socket.on("status_changed", function(data) {
            if (api_complete) {
                processEvent(data);
            }
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

    $rootScope.checkSocketConnectionInterval = setInterval(function() {
        if (job_socket.checkStatus() === 'error' || checkCount > 2) {
            // there's an error or we're stuck in a 'connecting' state. attempt to reconnect
            $log.debug('jobs page: initializing and restarting socket connections');
            job_socket = null;
            schedule_socket = null;
            openSockets();
            checkCount = 0;
        }
        else if (job_socket.checkStatus() === 'connecting') {
            checkCount++;
        }
        else {
            checkCount = 0;
        }
    }, 3000);

    function processEvent(event) {
        switch(event.status) {
            case 'running':
                running_scope.search('running_job');
                queued_scope.search('queued_job');
                break;
            case 'new':
            case 'pending':
            case 'waiting':
                queued_scope.search('queued_job');
                completed_scope.search('completed_job');
                break;
            case 'successful':
            case 'failed':
            case 'error':
            case 'canceled':
                completed_scope.search('completed_job');
                running_scope.search('running_job');
                queued_scope.search('queued_job');
        }
    }

    LoadBreadCrumbs();

    if ($scope.removeListLoaded) {
        $scope.removeListLoaded();
    }
    $scope.removeListLoaded = $scope.$on('listLoaded', function() {
        listCount++;
        if (listCount === 4) {
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

        if (CompletedJobsList.fields.type) {
            CompletedJobsList.fields.type.searchOptions = $scope.type_choices;
        }
        if (RunningJobsList.fields.type) {
            RunningJobsList.fields.type.searchOptions = $scope.type_choices;
        }
        if (QueuedJobsList.fields.type) {
            QueuedJobsList.fields.type.searchOptions = $scope.type_choices;
        }
        if ($routeParams.status) {
            search_params[CompletedJobsList.iterator + 'SearchField'] = 'status';
            search_params[CompletedJobsList.iterator + 'SelectShow'] = true;
            search_params[CompletedJobsList.iterator + 'SearchSelectOpts'] = CompletedJobsList.fields.status.searchOptions;
            search_params[CompletedJobsList.iterator + 'SearchFieldLabel'] = CompletedJobsList.fields.status.label.replace(/<br\>/g,' ');
            search_params[CompletedJobsList.iterator + 'SearchType'] = '';
            for (opt in CompletedJobsList.fields.status.searchOptions) {
                if (CompletedJobsList.fields.status.searchOptions[opt].value === $routeParams.status) {
                    search_params[CompletedJobsList.iterator + 'SearchSelectValue'] = CompletedJobsList.fields.status.searchOptions[opt];
                    break;
                }
            }
        }
        completed_scope = $scope.$new(true);
        completed_scope.showJobType = true;
        LoadJobsScope({
            parent_scope: $scope,
            scope: completed_scope,
            list: CompletedJobsList,
            id: 'completed-jobs',
            url: GetBasePath('unified_jobs') + '?or__status=successful&or__status=failed&or__status=error&or__status=canceled',
            searchParams: search_params,
            pageSize: max_rows
        });
        running_scope = $scope.$new(true);
        LoadJobsScope({
            parent_scope: $scope,
            scope: running_scope,
            list: RunningJobsList,
            id: 'active-jobs',
            url: GetBasePath('unified_jobs') + '?status=running',
            pageSize: max_rows
        });
        queued_scope = $scope.$new(true);
        LoadJobsScope({
            parent_scope: $scope,
            scope: queued_scope,
            list: QueuedJobsList,
            id: 'queued-jobs',
            url: GetBasePath('unified_jobs') + '?or__status=pending&or__status=waiting&or__status=new',
            pageSize: max_rows
        });
        scheduled_scope = $scope.$new(true);
        LoadSchedulesScope({
            parent_scope: $scope,
            scope: scheduled_scope,
            list: ScheduledJobsList,
            id: 'scheduled-jobs',
            url: GetBasePath('schedules') + '?next_run__isnull=false',
            pageSize: max_rows
        });

        $scope.refreshJobs = function() {
            queued_scope.search('queued_job');
            running_scope.search('running_job');
            completed_scope.search('completed_job');
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
        if (docw > 1200) {
            // customize the container height and # of rows based on available viewport height
            available_height = $(window).height() - $('#main-menu-container .navbar').outerHeight() - 80;
            if (docw < 1350) {
                available_height = (available_height < 800) ? 800 : available_height;
            } else {
                available_height = (available_height < 550) ? 550 : available_height;
            }
            $log.debug('available_height: ' + available_height);
            $('.jobs-list-container').each(function() {
                $(this).height(Math.floor(available_height / 2));
            });
            search_row = Math.max($('.search-row:eq(0)').outerHeight(), 50);
            page_row = Math.max($('.page-row:eq(0)').outerHeight(), 33);
            header = Math.max($('#completed_jobs_table thead').height(), 24);
            height = Math.floor(available_height / 2) - header - page_row - search_row - 30;
            row_height = (docw < 1350) ? 47 : 44;
            max_rows = Math.floor(height / row_height);
            max_rows = (max_rows < 5) ? 5 : max_rows;
        }
        else {
            // when width < 1240px || height < 800px put things back to their default state
            $('.jobs-list-container').each(function() {
                $(this).css({ 'height': 'auto' });
            });
            max_rows = 5;
        }
        $log.debug('max_rows: ' + max_rows);
    }

    // Set container height and return the number of allowed rows
    function resizeContainers() {
        setHeight();
        completed_scope[CompletedJobsList.iterator + '_page_size'] = max_rows;
        completed_scope.changePageSize(CompletedJobsList.name, CompletedJobsList.iterator);
        running_scope[RunningJobsList.iterator + '_page_size'] = max_rows;
        running_scope.changePageSize(RunningJobsList.name, RunningJobsList.iterator);
        queued_scope[QueuedJobsList.iterator + '_page_size'] = max_rows;
        queued_scope.changePageSize(QueuedJobsList.name, QueuedJobsList.iterator);
        scheduled_scope[ScheduledJobsList.iterator + '_page_size'] = max_rows;
        scheduled_scope.changePageSize(ScheduledJobsList.name, ScheduledJobsList.iterator);
    }
}

JobsListController.$inject = ['$rootScope', '$log', '$scope', '$compile', '$routeParams', 'ClearScope', 'Breadcrumbs', 'LoadBreadCrumbs', 'LoadSchedulesScope', 'LoadJobsScope', 'RunningJobsList', 'CompletedJobsList',
    'QueuedJobsList', 'ScheduledJobsList', 'GetChoices', 'GetBasePath', 'Wait', 'Socket'];
