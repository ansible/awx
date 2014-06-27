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
    .factory('DashboardJobs', ['$rootScope', '$compile', 'Rest', 'GetBasePath', 'ProcessErrors', 'Wait',
        function ($rootScope, $compile) {
            return function (params) {

                var scope = params.scope,
                    target = params.target,
                    //dashboard = params.dashboard,

                    html, element;

                html = "<div class=\"panel panel-default\" style=\"border:none\">\n";
                html += "<div class=\"panel-body \">\n";

                html += "<table class=\"table table-bordered\">\n";
                html += "<tr>\n";
                html += "<td class=\"h5 col-lg-6 text-center\">Active Jobs</td>\n";
                html += "</tr>\n";
                html += "<tr>\n";
                html += "<td class=\"col-lg-8\">\n";

//---------------------------------------------------------------------------------------------------------
//html code from Jobs page's partial:
                html += "<div class=\"col-md-6 right-side\">\n";
                html += "<div class=\"jobs-list-container\">\n";
                html += "<div class=\"row search-row\">\n";
                html += "<div class=\"col-md-6\"><div class=\"title\">Active</div></div>\n";
                html += "<div class=\"col-md-6\" id=\"active-jobs-search-container\"></div>\n";
                html += "</div>\n";
                html += "<div class=\"job-list\" id=\"active-jobs-container\">\n";
                html += "<div id=\"active-jobs\" class=\"job-list-target\"></div>\n";
                html += "</div>\n";
                html += "</div>\n";
                html += "</div>\n";
//---------------------------------------------------------------------------------------------------------

                html += "</td>\n";
                html += "</tr>\n";
                html += "</table>\n";

                html += "</div>\n";
                html += "</div>\n";




                element = angular.element(document.getElementById(target));
                element.html(html);
                $compile(element)(scope);
                scope.$emit('WidgetLoaded');

            };
        }
    ]);