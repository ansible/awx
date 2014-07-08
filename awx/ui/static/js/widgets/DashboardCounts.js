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

                // html = "<div id=\"count-container\" class=\"count-container row\">\n";
                // html += "<table col-xs-12>\n";
                // html += "<tr>\n";
                // html += "<td class=\"  h2 text-center\" style=\"border:none\"><a href=/#/home/hosts>" + dashboard.hosts.total+"</a></td>\n";
                // html += "<td class=\"  h2 text-center\" style=\"border:none\"><a href=/#/home/hosts>"+dashboard.hosts.failed+"</a></td>\n";
                // html += "<td class=\"  h2 text-center\" style=\"border:none\"><a href=/#/inventories>"+dashboard.inventories.total+"</a></td>\n";
                // html += "<td class=\"  h2 text-center\" id=\"sync-failure\" style=\"border:none\"><a href=/#/inventories/?inventory_sources_with_failures>"+dashboard.inventories.inventory_failed+"</a></td>\n";
                // html += "<td class=\"  h2 text-center\" style=\"border:none\"><a href=/#/projects>"+dashboard.projects.total+"</a></td>\n";
                // html += "<td class=\"  h2 text-center\" style=\"border:none\"><a href=/#/projects>"+dashboard.projects.failed+"</a></td>\n";
                // html += "<td class=\"  h2 text-center\" style=\"border:none\"><a href=/#/users>"+dashboard.users.total+"</a></td>\n";
                // html += "</tr>\n";

                // html += "<tr>\n";
                // html += "<td class=\" h6 text-center\" style=\"border:none\">Hosts</td>\n";
                // html += "<td class=\" h6 col-lg-1 text-center\" style=\"border:none\">Failed Hosts</td>\n";
                // html += "<td class=\" h6 col-lg-1 text-center\" style=\"border:none\">Inventories</td>\n";
                // html += "<td class=\" h6 col-lg-1 text-center\" style=\"border:none\">Inventory Sync Failures</td>\n";
                // html += "<td class=\" h6 col-lg-1 text-center\" style=\"border:none\">Projects</td>\n";
                // html += "<td class=\" h6 col-lg-1 text-center\" style=\"border:none\">Project Sync Failures</td>\n";
                // html += "<td class=\" h6 col-lg-1 text-center\" style=\"border:none\">Users</td>\n";
                // html += "</tr>\n";
                // html += "</table>\n";
                // html += "</div>\n";


                html = "<div class=\"container\" >\n";

                html = "<div id=\"count-container\" class=\"count-container row\">\n";
                html += "<div class=\"h2 col-xs-4 col-sm-2 text-center\"><a href=/#/home/hosts>" + dashboard.hosts.total+"</a><br><h6>Hosts</h6></div>\n";
                html += "<div class=\"h2 col-xs-4 col-sm-2 text-center\"><a href=/#/home/hosts id=\"failed-hosts\">"+dashboard.hosts.failed+"</a><br><h6>Failed Hosts</h6></div>\n";
                html += "<div class=\"h2 col-xs-4 col-sm-2 text-center\"><a href=/#/inventories>"+dashboard.inventories.total+"</a><br><h6>Inventories</h6></div>\n";
                html += "<div class=\"h2 col-xs-4 col-sm-2 text-center\"><a href=/#/inventories/?inventory_sources_with_failures id=\"failed-inventories\">"+dashboard.inventories.inventory_failed+"</a><br><h6>Inventory Sync Failure</h6></div>\n";
                html += "<div class=\"h2 col-xs-4 col-sm-2 text-center\"><a href=/#/projects>"+dashboard.projects.total+"</a><br><h6>Projects</h6></div>\n";
                html += "<div class=\"h2 col-xs-4 col-sm-2 text-center\"><a href=/#/projects id=\"failed-projects\">"+dashboard.projects.failed+"</a><br><h6>Project Sync Failure</h6></div>\n";
                               // html += "<div class=\"h2  col-xs-4 col-sm-2 text-center\"><a href=/#/users>"+dashboard.users.total+"</a></div>\n";
                html += "</div>\n";

                            // html += "<div class=\"row\"> \n";
                            //         html += "<div class=\"h6  col-xs-4 col-sm-2 text-center\">Hosts</div>\n";
                            //         html += "<div class=\"h6  col-xs-4 col-sm-2 text-center\">Failed Hosts</div>\n";
                            //         html += "<div class=\"h6  col-xs-4 col-sm-2 text-center\">Inventories</div>\n";
                            //         html += "<div class=\"h6  col-xs-4 col-sm-2 text-center\">Inventory Sync Failures</div>\n";
                            //         html += "<div class=\"h6  col-xs-4 col-sm-2 text-center\">Projects</div>\n";
                            //         html += "<div class=\"h6  col-xs-4 col-sm-2 text-center\">Project Sync Failures</div>\n";
                            //         // html += "<div class=\"h6  col-xs-4 col-sm-2 text-center\">Users</div>\n";
                            // html += "</div>\n";
                html += "</div>\n";


                        // html = "<div id=\"count-container\" class=\"row\">\n";
                        //         // html+= "<div class=\"col-lg-6\">\n";
                        //                 html = "<table class=\"col-sm-6\">\n";
                        //                 html += "<tr>\n";
                        //                 html += "<td class=\"h2  text-center\"><a href=/#/home/hosts>" + dashboard.hosts.total+"</a></td>\n";
                        //                 html += "<td class=\"h2  text-center\"><a href=/#/home/hosts>"+dashboard.hosts.failed+"</a></td>\n";
                        //                 html += "<td class=\"h2 text-center\"><a href=/#/inventories>"+dashboard.inventories.total+"</a></td>\n";

                        //                 html += "</tr>\n";

                        //                 html += "<tr>\n";
                        //                 html += "<td class=\"h6  text-center\">Hosts</td>\n";
                        //                 html += "<td class=\"h6 text-center\">Failed Hosts</td>\n";
                        //                 html += "<td class=\"h6   text-center\">Inventories</td>\n";

                        //                 html += "</tr>\n";
                        //                 html += "</table>\n";
                        //         // html += "</div>\n";

                        //        // html+= "<div >\n";
                        //                 html += "<table class=\"col-sm-6\">\n";
                        //                 html += "<tr>\n";
                        //                 html += "<td class=\"h2  text-center\" id=\"sync-failure\"><a href=/#/inventories/?inventory_sources_with_failures>"+dashboard.inventories.inventory_failed+"</a></td>\n";
                        //                 html += "<td class=\"h2  text-center\"><a href=/#/projects>"+dashboard.projects.total+"</a></td>\n";
                        //                 html += "<td class=\"h2  text-center\"><a href=/#/projects>"+dashboard.projects.failed+"</a></td>\n";
                        //                 html += "<td class=\"h2  text-center\"><a href=/#/users>"+dashboard.users.total+"</a></td>\n";

                        //                 html += "</tr>\n";

                        //                 html += "<tr>\n";
                        //                 html += "<td class=\"h6    text-center\">Inventory Sync Failures</td>\n";
                        //                 html += "<td class=\"h6    text-center\">Projects</td>\n";
                        //                 html += "<td class=\"h6    text-center\">Project Sync Failures</td>\n";
                        //                 html += "<td class=\"h6   text-center\">Users</td>\n";

                        //                 html += "</tr>\n";
                        //                 html += "</table>\n";
                        //         // html += "</div>\n";
                        // html += "</div>\n";





                element = angular.element(document.getElementById(target));
                element.html(html);
                $compile(element)(scope);
                if(dashboard.hosts.failed>0 ){
                    $('#failed-hosts').html("<a style=\"color:red\" href=/#/home/hosts id=\"failed-hosts\">"+dashboard.hosts.failed+"</a>");
                }
                if(dashboard.inventories.inventory_failed>0 ){
                    $('#failed-inventories').html("<a style=\"color:red\" href=/#/inventories/?inventory_sources_with_failures id=\"failed-inventories\">"+dashboard.inventories.inventory_failed+"</a>");
                }
                if(dashboard.projects.failed>0 ){
                    $('#failed-projects').html("<a style=\"color:red\" href=/#/projects id=\"failed-projects\">"+dashboard.projects.failed+"</a>");
                }
                scope.$emit('WidgetLoaded');




            };
        }
    ]);