/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 * JobStatus.js
 *
 * Dashboard widget showing object counts and license availability.
 *
 */

'use strict';

angular.module('JobStatusWidget', ['RestServices', 'Utilities'])
    .factory('JobStatus', ['$rootScope', '$compile', 'Rest', 'GetBasePath', 'ProcessErrors', 'Wait', function ($rootScope, $compile) {
        return function (params) {
            var scope = params.scope,
                target = params.target,
                html = '', element;

            html += "<ul id=\"job_status_tabs\" class=\"nav nav-tabs\">\n";
            html += "<li class=\"active\"><a id=\"active_jobs_link\" ng-click=\"toggleTab($event, 'active_jobs_link', 'job_status_tabs')\"\n";
            html += " href=\"#active-jobs-tab\" data-toggle=\"tab\">Jobs</a></li>\n";
            html += "<li><a id=\"scheduled_jobs_link\" ng-click=\"toggleTab($event, 'scheduled_jobs_link', 'job_status_tabs')\"\n";
            html += "href=\"#scheduled-jobs-tab\" data-toggle=\"tab\">Schedule</a></li>\n";
            html += "</ul>\n";
            html += "<div class=\"tab-content\">\n";
            html += "<div class=\"tab-pane active\" id=\"active-jobs-tab\"></div>\n";
            html += "<div class=\"tab-pane\" id=\"scheduled-jobs-tab\"></div>\n";
            html += "<div class=\"tab-pane\" id=\"schedules-tab\"></div>\n";
            html += "</div>\n";


        };
    }]);