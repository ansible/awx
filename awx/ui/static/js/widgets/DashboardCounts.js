/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 * Dashboard.js
 *
 * The dashboard widget with stats across the top
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


                html = "<div class=\"container\" >\n";

                html = "<div id=\"count-container\" class=\"count-container row\">\n";
                html += "<div class=\"h2 col-xs-4 col-sm-2 text-center\"><a href=\"/#/home/hosts\">"+ dashboard.hosts.total+"</a><br><h6>Hosts</h6></div>\n";
                html += "<div class=\"h2 col-xs-4 col-sm-2 text-center\"><a href=\"/#/home/hosts/?has_active_failures=true\" id=\"failed-hosts\">"+dashboard.hosts.failed+"</a><br><h6>Failed Hosts</h6></div>\n";
                html += "<div class=\"h2 col-xs-4 col-sm-2 text-center\"><a href=\"/#/inventories\">"+dashboard.inventories.total+"</a><br><h6>Inventories</h6></div>\n";
                html += "<div class=\"h2 col-xs-4 col-sm-2 text-center\"><a href=\"/#/inventories/?inventory_sources_with_failures\" id=\"failed-inventories\">"+dashboard.inventories.inventory_failed+"</a><br><h6>Inventory Sync Failures</h6></div>\n";
                html += "<div class=\"h2 col-xs-4 col-sm-2 text-center\"><a href=\"/#/projects\">"+dashboard.projects.total+"</a><br><h6>Projects</h6></div>\n";
                html += "<div class=\"h2 col-xs-4 col-sm-2 text-center\"><a href=\"/#/projects/?status=failed\" id=\"failed-projects\">"+dashboard.projects.failed+"</a><br><h6>Project Sync Failures</h6></div>\n";
                               // html += "<div class=\"h2  col-xs-4 col-sm-2 text-center\"><a href=/#/users>"+dashboard.users.total+"</a></div>\n";
                html += "</div>\n";

                html += "</div>\n";


                element = angular.element(document.getElementById(target));
                element.html(html);
                $compile(element)(scope);
                if(dashboard.hosts.failed>0 ){
                    $('#failed-hosts').replaceWith("<a style=\"color:#aa0000\" href=\"/#/home/hosts/?has_active_failures=true\" id=\"failed-hosts\">"+dashboard.hosts.failed+"</a>");
                }
                if(dashboard.inventories.inventory_failed>0 ){
                    $('#failed-inventories').replaceWith("<a style=\"color:#aa0000\" href=/#/inventories/?inventory_sources_with_failures id=\"failed-inventories\">"+dashboard.inventories.inventory_failed+"</a>");
                }
                if(dashboard.projects.failed>0 ){
                    $('#failed-projects').replaceWith("<a style=\"color:#aa0000\" href=\"/#/projects/?status=failed\" id=\"failed-projects\">"+dashboard.projects.failed+"</a>");
                }
                scope.$emit('WidgetLoaded');

            };
        }
    ]);