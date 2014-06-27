/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 * Dashboard.js
 *
 * The new dashboard
 *
 */

'use strict';

angular.module('DashboardCountsWidget', ['RestServices', 'Utilities'])
    .factory('DashboardCounts', ['$rootScope', '$compile', 'Rest', 'GetBasePath', 'ProcessErrors', 'Wait',
        function ($rootScope, $compile) {
            return function (params) {

                var scope = params.scope,
                    target = params.target,
                    dashboard = params.dashboard,

                    html, element;

                html = "<div class=\"panel panel-default\" style=\"border:none\">\n";
                //html += "<div class=\"panel-heading\">New Dashboard</div>\n";
                html += "<div class=\"panel-body \">\n";
                html += "<table>\n";

                html += "<tr>\n";
                html += "<td class=\"h1 col-lg-1 text-center\"><a href=/#/home/hosts>" + dashboard.hosts.total+"</a></td>\n";
                html += "<td class=\"h1 col-lg-1-1 text-center\"><a href=/#/home/hosts>"+dashboard.hosts.failed+"</a></td>\n";
                html += "<td class=\"h1 col-lg-1-1 text-center\"><a href=/#/inventories>"+dashboard.inventories.total+"</a></td>\n";
                html += "<td class=\"h1 col-lg-1 text-center\" id=\"sync-failure\"><a href=/#/inventories/?inventory_sources_with_failures>"+dashboard.inventories.inventory_failed+"</a></td>\n";
                html += "<td class=\"h1 col-lg-1 text-center\"><a href=/#/projects>"+dashboard.projects.total+"</a></td>\n";
                html += "<td class=\"h1 col-lg-1 text-center\"><a href=/#/projects>"+dashboard.projects.failed+"</a></td>\n";
                html += "<td class=\"h1 col-lg-1 text-center\"><a href=/#/users>"+dashboard.users.total+"</a></td>\n";
                html += "</tr>\n";

                html += "<tr>\n";
                html += "<td class=\"h5 col-lg-1 text-center\">Hosts</td>\n";
                html += "<td class=\"h5 col-lg-1 text-center\">Failed Hosts</td>\n";
                html += "<td class=\"h5 col-lg-1 text-center\">Inventories</td>\n";
                html += "<td class=\"h5 col-lg-1 text-center\">Inventory Sync Failures</td>\n";
                html += "<td class=\"h5 col-lg-1 text-center\">Projects</td>\n";
                html += "<td class=\"h5 col-lg-1 text-center\">Project Sync Failures</td>\n";
                html += "<td class=\"h5 col-lg-1 text-center\">Users</td>\n";
                html += "</tr>\n";
                html += "</table>\n";





                element = angular.element(document.getElementById(target));
                element.html(html);
                $compile(element)(scope);

                scope.$emit('WidgetLoaded');

            };
        }
    ]);