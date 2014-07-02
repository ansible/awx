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

                html = "<div id=\"count-container\" class=\"count-container\">\n";
                html += "<table>\n";
                html += "<tr>\n";
                html += "<td class=\"  h2 text-center\" style=\"border:none\"><a href=/#/home/hosts>" + dashboard.hosts.total+"</a></td>\n";
                html += "<td class=\"  h2 text-center\" style=\"border:none\"><a href=/#/home/hosts>"+dashboard.hosts.failed+"</a></td>\n";
                html += "<td class=\"  h2 text-center\" style=\"border:none\"><a href=/#/inventories>"+dashboard.inventories.total+"</a></td>\n";
                html += "<td class=\"  h2 text-center\" id=\"sync-failure\" style=\"border:none\"><a href=/#/inventories/?inventory_sources_with_failures>"+dashboard.inventories.inventory_failed+"</a></td>\n";
                html += "<td class=\"  h2 text-center\" style=\"border:none\"><a href=/#/projects>"+dashboard.projects.total+"</a></td>\n";
                html += "<td class=\"  h2 text-center\" style=\"border:none\"><a href=/#/projects>"+dashboard.projects.failed+"</a></td>\n";
                html += "<td class=\"  h2 text-center\" style=\"border:none\"><a href=/#/users>"+dashboard.users.total+"</a></td>\n";
                html += "</tr>\n";

                html += "<tr>\n";
                html += "<td class=\" h6 col-lg-1 text-center\" style=\"border:none\">Hosts</td>\n";
                html += "<td class=\" h6 col-lg-1 text-center\" style=\"border:none\">Failed Hosts</td>\n";
                html += "<td class=\" h6 col-lg-1 text-center\" style=\"border:none\">Inventories</td>\n";
                html += "<td class=\" h6 col-lg-1 text-center\" style=\"border:none\">Inventory Sync Failures</td>\n";
                html += "<td class=\" h6 col-lg-1 text-center\" style=\"border:none\">Projects</td>\n";
                html += "<td class=\" h6 col-lg-1 text-center\" style=\"border:none\">Project Sync Failures</td>\n";
                html += "<td class=\" h6 col-lg-1 text-center\" style=\"border:none\">Users</td>\n";
                html += "</tr>\n";
                html += "</table>\n";
                html += "</div>\n";


                // html = "<div class=\"container\" >\n";

                            // html = "<div class=\"row\"> \n";
                            //         html += "<div class=\"h2 col-xs-1 text-center\"><a href=/#/home/hosts>" + dashboard.hosts.total+"</a></div>\n";
                            //         html += "<div class=\"h2 col-xs-1 text-center\"><a href=/#/home/hosts>"+dashboard.hosts.failed+"</a></div>\n";
                            //         html += "<div class=\"h2 col-xs-1 text-center\"><a href=/#/inventories>"+dashboard.inventories.total+"</a></div>\n";
                            //         html += "<div class=\"h2 col-xs-1 text-center\" id=\"sync-failure\"><a href=/#/inventories/?inventory_sources_with_failures>"+dashboard.inventories.inventory_failed+"</a></div>\n";
                            //         html += "<div class=\"h2 col-xs-1 text-center\"><a href=/#/projects>"+dashboard.projects.total+"</a></div>\n";
                            //         html += "<div class=\"h2 col-xs-1 text-center\"><a href=/#/projects>"+dashboard.projects.failed+"</a></div>\n";
                            //         html += "<div class=\"h2 col-xs-1 text-center\"><a href=/#/users>"+dashboard.users.total+"</a></div>\n";
                            // html += "</div>\n";

                            // html = "<div class=\"row\"> \n";
                            //         html += "<div class=\"h6 col-xs-1 text-center\">Hosts</div>\n";
                            //         html += "<div class=\"h6 col-xs-1 text-center\">Failed Hosts</div>\n";
                            //         html += "<div class=\"h6 col-xs-1 text-center\">Inventories</div>\n";
                            //         html += "<div class=\"h6 col-xs-1 text-center\">Inventory Sync Failures</div>\n";
                            //         html += "<div class=\"h6 col-xs-1 text-center\">Projects</div>\n";
                            //         html += "<div class=\"h6 col-xs-1 text-center\">Project Sync Failures</div>\n";
                            //         html += "<div class=\"h6 col-xs-1 text-center\">Users</div>\n";
                            // html += "</div>\n";
                   // html += "</div>\n";


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

                scope.$emit('WidgetLoaded');




            };
        }
    ]);