/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 * Dashboard.js
 *
 * The new dashboard
 *
 */

'use strict';

angular.module('DashboardJobsWidget', ['RestServices', 'Utilities'])
.factory('DashboardJobs', ['$rootScope', '$compile', 'LoadSchedulesScope', 'LoadJobsScope', 'JobsList', 'ScheduledJobsList', 'GetChoices', 'GetBasePath',
    function ($rootScope, $compile, LoadSchedulesScope, LoadJobsScope, JobsList, ScheduledJobsList, GetChoices, GetBasePath) {
    return function (params) {
        var scope = params.scope,
            target = params.target,
            choicesCount = 0,
            listCount = 0,
            jobs_scope = scope.$new(true),
            scheduled_scope = scope.$new(true),
            max_rows,
            html, e;

        html = '';
        html += "<div class=\"dashboard-jobs-list-container\">\n";
        html += "<ul id=\"job_status_tabs\" class=\"nav nav-tabs\">\n";
        html += "<li class=\"active\"><a id=\"active_jobs_link\" ng-click=\"toggleTab($event, 'active_jobs_link', 'job_status_tabs')\"\n";
        html += " href=\"#active-jobs-tab\" data-toggle=\"tab\">Jobs</a></li>\n";
        html += "<li><a id=\"scheduled_jobs_link\" ng-click=\"toggleTab($event, 'scheduled_jobs_link', 'job_status_tabs')\"\n";
        html += "href=\"#scheduled-jobs-tab\" data-toggle=\"tab\">Schedule</a></li>\n";
        html += "</ul>\n";
        html += "<div  id=\"dashboard-tab-content\" class=\"tab-content \">\n";
        html += "<div class=\"tab-pane active\" id=\"active-jobs-tab\">\n";
        html += "<div class=\"row search-row\">\n";
        html += "<div class=\"col-lg-6 col-md-6\" id=\"active-jobs-search-container\"></div>\n";
        html += "</div>\n"; //row
        html += "<div class=\"job-list\" id=\"active-jobs-container\">\n";
        html += "<div id=\"active-jobs\" class=\"job-list-target\"></div>\n";
        html += "</div>\n"; //list
        html += "</div>\n"; //active-jobs-tab
        html += "<div class=\"tab-pane\" id=\"scheduled-jobs-tab\"></div>\n";
        html += "</div>\n"; // jobs-list-container
        html += "</div>\n";

        e = angular.element(document.getElementById(target));
        e.html(html);
        $compile(e)(scope);

        if (scope.removeListLoaded) {
            scope.removeListLoaded();
        }
        scope.removeListLoaded = scope.$on('listLoaded', function() {
            listCount++;
            if (listCount === 1) {
                //api_complete = true;
                scope.$emit('WidgetLoaded');
            }
        });

        // After all choices are ready, load up the lists and populate the page
        if (scope.removeBuildJobsList) {
            scope.removeBuildJobsList();
        }
        scope.removeBuildJobsList = scope.$on('buildJobsList', function() {
            if (JobsList.fields.type) {
                JobsList.fields.type.searchOptions = scope.type_choices;
            }
            LoadJobsScope({
                parent_scope: scope,
                scope: jobs_scope,
                list: JobsList,
                id: 'active-jobs',
                url: GetBasePath('unified_jobs') + '?status__in=running,completed,failed,successful,error,canceled',
                pageSize: max_rows
            });
            LoadSchedulesScope({
                parent_scope: scope,
                scope: scheduled_scope,
                list: ScheduledJobsList,
                id: 'scheduled-jobs-tab',
                url: GetBasePath('schedules') + '?next_run__isnull=false',
                pageSize: max_rows
            });

            $(window).resize(_.debounce(function() {
                resizeDashboardJobsWidget();
            }, 500));
        });

        if (scope.removeChoicesReady) {
            scope.removeChoicesReady();
        }
        scope.removeChoicesReady = scope.$on('choicesReady', function() {
            choicesCount++;
            if (choicesCount === 2) {
                setDashboardJobsHeight();
                scope.$emit('buildJobsList');
            }
        });

        GetChoices({
            scope: scope,
            url: GetBasePath('unified_jobs'),
            field: 'status',
            variable: 'status_choices',
            callback: 'choicesReady'
        });

        GetChoices({
            scope: scope,
            url: GetBasePath('unified_jobs'),
            field: 'type',
            variable: 'type_choices',
            callback: 'choicesReady'
        });



     // Set the height of each container and calc max number of rows containers can hold
        function setDashboardJobsHeight() {
            var docw = $(window).width(),
                box_height, available_height, search_row, page_row, height, header, row_height;

            available_height = Math.floor(($(window).height() - $('#main-menu-container .navbar').outerHeight() - $('#count-container').outerHeight() - 93)/2);
            $('.dashboard-jobs-list-container').height(available_height);
            search_row = Math.max($('.search-row:eq(0)').outerHeight(), 50);
            page_row = Math.max($('.page-row:eq(0)').outerHeight(), 33);
            header = Math.max($('#completed_jobs_table thead').height(), 41);
            height = Math.floor(available_height) - header - page_row - search_row -30 ;
            if (docw < 765 && docw >= 493) {
                row_height = 27;
            }
            else if (docw < 493) {
                row_height = 47;
            }
            else if (docw < 865) {
                row_height = 87;
            }
            else if (docw < 925) {
                row_height = 67;
            }
            else if (docw < 1415) {
                row_height = 47;
            }
            else {
                row_height = 27;
            }
            max_rows = Math.floor(height / row_height);
            if (max_rows < 5){
                box_height = header+page_row + search_row + 40 + (5 * row_height);
                if (docw < 1140) {
                    box_height += 40;
                }
                $('.dashboard-jobs-list-container').height(box_height);
                max_rows = 5;
            }
        }

        // Set container height and return the number of allowed rows
        function resizeDashboardJobsWidget() {
            setDashboardJobsHeight();
            jobs_scope[JobsList.iterator + '_page_size'] = max_rows;
            jobs_scope.changePageSize(JobsList.name, JobsList.iterator);
            scheduled_scope[ScheduledJobsList.iterator + '_page_size'] = max_rows;
            scheduled_scope.changePageSize(ScheduledJobsList.name, ScheduledJobsList.iterator);
        }



    };
}
]);
