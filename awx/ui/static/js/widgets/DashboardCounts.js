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

                    function createHTML(html){
                        var docw = $(window).width();
                        if(docw<768){

                                html = "<div id=\"dash-count-carousel\" class=\"carousel slide\" data-interval=\"1000\" data-ride=\"carousel\">\n" ;
                                // html += " <!-- Indicators -->\n";
                                html += "<ol class=\"carousel-indicators\">\n";
                                html += "<li data-target=\"#dash-count-carousel\" data-slide-to=\"0\" class=\"active\"></li>\n";
                                html += "<li data-target=\"#dash-count-carousel\" data-slide-to=\"1\"></li>\n";
                                html += "<li data-target=\"#dash-count-carousel\" data-slide-to=\"2\"></li>\n";
                                html += "</ol>\n";

                                //<!-- Wrapper for slides -->
                                //html += "<div class=\"carousel-inner\">\n" ;
                                html += "<div class=\"carousel-inner\">\n" ;
                                html += "<div class=\"item active\">\n" ;
                                html += "<img src=\"http://placehold.it/1200x480\" alt=\"\" />\n" ;
                                html += "<div class=\"carousel-caption\">\n" ;
                                html += "<p>Caption text here</p>\n" ;
                                html += "</div>\n" ;
                                html += "</div>\n" ;
                                html += "<div class=\"item\">\n" ;
                                html += "<img src=\"http://placehold.it/1200x480\" alt=\"\" />\n" ;
                                html += "<div class=\"carousel-caption\">\n" ;
                                html += "<p>Caption text here</p>\n" ;
                                html += "</div>\n" ;
                                html += "</div>\n" ;
                                html += "<div class=\"item\">\n" ;
                                html += "<img src=\"http://placehold.it/1200x480\" alt=\"\" />\n" ;
                                html += "<div class=\"carousel-caption\">\n" ;
                                html += "<p>Caption text here</p>\n" ;
                                html += "</div>\n" ;
                                html += "</div>\n" ;
                                html += "<div class=\"item\">\n" ;
                                html += "<img src=\"http://placehold.it/1200x480\" alt=\"\" />\n" ;
                                html += "<div class=\"carousel-caption\">\n" ;
                                html += "<p>Caption text here</p>\n" ;
                                html += "</div>\n" ;
                                html += "</div>\n" ;
                                html += "</div>\n" ;

                               // html += \"<!-- Controls -->\n" ;
                                html += "<a class=\" carousel-control left\"  href=\"#dash-count-carousel\" role=\"button\" data-slide=\"prev\">\n" ;
                                html += "<span class=\"icon-prev\" onclick=\"javascript:$(\'.carousel\'').carousel(\'prev\'')\"></span>\n" ;
                                html += "</a>\n" ;
                                html += "<a class=\"carousel-control right\"  href=\"#dash-count-carousel\" role=\"button\" data-slide=\"next\">\n" ;
                                html += "<span class=\"icon-next\"></span>\n" ;
                                html += "</a>\n" ;
                                html += "</div>\n" ;
// <!-- Controls -->
//   <a class="left carousel-control" href="#carousel-example-generic" role="button" data-slide="prev">
//     <span class="glyphicon glyphicon-chevron-left"></span>
//   </a>
//   <a class="right carousel-control" href="#carousel-example-generic" role="button" data-slide="next">
//     <span class="glyphicon glyphicon-chevron-right"></span>
//   </a>
// </div>
                                // $('.carousel').carousel({
                                //   interval: 2000
                                // })


                        }
                        else{
                            html = "<div id=\"count-container\" class=\"panel-body\" style=\"borderBottom:thick solid #0000FF\">\n";
                            html += "<table class=\"table-bordered\">\n";
                            html += "<tr>\n";
                            html += "<td class=\"h2 col-lg-1 text-center\"><a href=/#/home/hosts>" + dashboard.hosts.total+"</a></td>\n";
                            html += "<td class=\"h2 col-lg-1-1 text-center\"><a href=/#/home/hosts>"+dashboard.hosts.failed+"</a></td>\n";
                            html += "<td class=\"h2 col-lg-1-1 text-center\"><a href=/#/inventories>"+dashboard.inventories.total+"</a></td>\n";
                            html += "<td class=\"h2 col-lg-1 text-center\" id=\"sync-failure\"><a href=/#/inventories/?inventory_sources_with_failures>"+dashboard.inventories.inventory_failed+"</a></td>\n";
                            html += "<td class=\"h2 col-lg-1 text-center\"><a href=/#/projects>"+dashboard.projects.total+"</a></td>\n";
                            html += "<td class=\"h2 col-lg-1 text-center\"><a href=/#/projects>"+dashboard.projects.failed+"</a></td>\n";
                            html += "<td class=\"h2 col-lg-1 text-center\"><a href=/#/users>"+dashboard.users.total+"</a></td>\n";
                            html += "</tr>\n";

                            html += "<tr>\n";
                            html += "<td class=\"h6 col-lg-1 text-center\">Hosts</td>\n";
                            html += "<td class=\"h6 col-lg-1 text-center\">Failed Hosts</td>\n";
                            html += "<td class=\"h6 col-lg-1 text-center\">Inventories</td>\n";
                            html += "<td class=\"h6 col-lg-1 text-center\">Inventory Sync Failures</td>\n";
                            html += "<td class=\"h6 col-lg-1 text-center\">Projects</td>\n";
                            html += "<td class=\"h6 col-lg-1 text-center\">Project Sync Failures</td>\n";
                            html += "<td class=\"h6 col-lg-1 text-center\">Users</td>\n";
                            html += "</tr>\n";
                            html += "</table>\n";
                            html += "</div>\n";
                            // html += "<hr>\n";

                        }


                        return html;
                    }






                // html = "<div id=\"count-container\" class=\"panel-body visible-xs-block\" style=\"border:none\">\n";
                // html += "<table>table1\n";
                // html += "<tr>\n";
                // html += "<td class=\"h1 col-lg-1 text-center\"><a href=/#/home/hosts>" + dashboard.hosts.total+"</a></td>\n";
                // html += "<td class=\"h1 col-lg-1-1 text-center\"><a href=/#/home/hosts>"+dashboard.hosts.failed+"</a></td>\n";
                // html += "<td class=\"h1 col-lg-1-1 text-center\"><a href=/#/inventories>"+dashboard.inventories.total+"</a></td>\n";
                // html += "<td class=\"h1 col-lg-1 text-center\" id=\"sync-failure\"><a href=/#/inventories/?inventory_sources_with_failures>"+dashboard.inventories.inventory_failed+"</a></td>\n";
                // html += "<td class=\"h1 col-lg-1 text-center\"><a href=/#/projects>"+dashboard.projects.total+"</a></td>\n";
                // html += "<td class=\"h1 col-lg-1 text-center\"><a href=/#/projects>"+dashboard.projects.failed+"</a></td>\n";
                // html += "<td class=\"h1 col-lg-1 text-center\"><a href=/#/users>"+dashboard.users.total+"</a></td>\n";
                // html += "</tr>\n";

                // html += "<tr>\n";
                // html += "<td class=\"h5 col-lg-1 text-center\">Hosts</td>\n";
                // html += "<td class=\"h5 col-lg-1 text-center\">Failed Hosts</td>\n";
                // html += "<td class=\"h5 col-lg-1 text-center\">Inventories</td>\n";
                // html += "<td class=\"h5 col-lg-1 text-center\">Inventory Sync Failures</td>\n";
                // html += "<td class=\"h5 col-lg-1 text-center\">Projects</td>\n";
                // html += "<td class=\"h5 col-lg-1 text-center\">Project Sync Failures</td>\n";
                // html += "<td class=\"h5 col-lg-1 text-center\">Users</td>\n";
                // html += "</tr>\n";
                // html += "</table>\n";
                // html += "</div>\n";
                // html += "<hr>\n";

//--------------------------------------------------------------------------------------------------------------------
                // html = "<div id=\"count-container\" class=\"panel-body visible-md-block\" style=\"border:none\">\n";
                // html += "<table>table2\n";
                // html += "<tr>\n";
                // html += "<td class=\"h1 col-lg-1 text-center\"><a href=/#/home/hosts>" + dashboard.hosts.total+"</a></td>\n";
                // html += "<td class=\"h1 col-lg-1-1 text-center\"><a href=/#/home/hosts>"+dashboard.hosts.failed+"</a></td>\n";
                // html += "<td class=\"h1 col-lg-1-1 text-center\"><a href=/#/inventories>"+dashboard.inventories.total+"</a></td>\n";
                // html += "<td class=\"h1 col-lg-1 text-center\" id=\"sync-failure\"><a href=/#/inventories/?inventory_sources_with_failures>"+dashboard.inventories.inventory_failed+"</a></td>\n";
                // html += "<td class=\"h1 col-lg-1 text-center\"><a href=/#/projects>"+dashboard.projects.total+"</a></td>\n";
                // html += "<td class=\"h1 col-lg-1 text-center\"><a href=/#/projects>"+dashboard.projects.failed+"</a></td>\n";
                // html += "<td class=\"h1 col-lg-1 text-center\"><a href=/#/users>"+dashboard.users.total+"</a></td>\n";
                // html += "</tr>\n";

                // html += "<tr>\n";
                // html += "<td class=\"h5 col-lg-1 text-center\">Hosts</td>\n";
                // html += "<td class=\"h5 col-lg-1 text-center\">Failed Hosts</td>\n";
                // html += "<td class=\"h5 col-lg-1 text-center\">Inventories</td>\n";
                // html += "<td class=\"h5 col-lg-1 text-center\">Inventory Sync Failures</td>\n";
                // html += "<td class=\"h5 col-lg-1 text-center\">Projects</td>\n";
                // html += "<td class=\"h5 col-lg-1 text-center\">Project Sync Failures</td>\n";
                // html += "<td class=\"h5 col-lg-1 text-center\">Users</td>\n";
                // html += "</tr>\n";
                // html += "</table>\n";
                // html += "</div>\n";
                // html += "<hr>\n";
//--------------------------------------------------------------------------------------------------------------------
                element = angular.element(document.getElementById(target));
                element.html(createHTML(html));
                $compile(element)(scope);

                scope.$emit('WidgetLoaded');


                //window.onresize = scaleForSmallDevices;

                function scaleForSmallDevices(){
                    var docw = $(window).width();
                    if(docw<600){
                        alert('success');
                    }

                };

            };
        }
    ]);