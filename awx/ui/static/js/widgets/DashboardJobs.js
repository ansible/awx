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
            max_rows = 15,
            html, e;

        html = '';
        html += "<ul id=\"job_status_tabs\" class=\"nav nav-tabs\">\n";
        html += "<li class=\"active\"><a id=\"active_jobs_link\" ng-click=\"toggleTab($event, 'active_jobs_link', 'job_status_tabs')\"\n";
        html += " href=\"#active-jobs-tab\" data-toggle=\"tab\">Jobs</a></li>\n";
        html += "<li><a id=\"scheduled_jobs_link\" ng-click=\"toggleTab($event, 'scheduled_jobs_link', 'job_status_tabs')\"\n";
        html += "href=\"#scheduled-jobs-tab\" data-toggle=\"tab\">Schedule</a></li>\n";
        html += "</ul>\n";
        html += "<div class=\"tab-content\">\n";
        html += "<div class=\"tab-pane active\" id=\"active-jobs-tab\"></div>\n";
        html += "<div class=\"tab-pane\" id=\"scheduled-jobs-tab\"></div>\n";
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
                id: 'active-jobs-tab',
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
        });

        if (scope.removeChoicesReady) {
            scope.removeChoicesReady();
        }
        scope.removeChoicesReady = scope.$on('choicesReady', function() {
            choicesCount++;
            if (choicesCount === 2) {
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
    };
}]);