/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 * Dashboard.js
 *
 * The new dashboard
 *
 */

'use strict';

angular.module('JobStatusGraphWidget', ['RestServices', 'Utilities'])
    .factory('JobStatusGraph', ['$rootScope', '$compile', '$location' , 'Rest', 'GetBasePath', 'ProcessErrors', 'Wait',
        function ($rootScope, $compile , $location, Rest, GetBasePath, ProcessErrors, Wait) {
            return function (params) {

                var scope = params.scope,
                    target = params.target,
                    // dashboard = params.dashboard,
                    html, element, url;

                html = "<div class=\"graph-container\">\n";

                html +="<div class=\"row\">\n";
                html += "<div class=\"h6 col-xs-8 text-center\"><b>Job Status</b></div>\n";

                html += "<div class=\"h6 col-xs-2 \">\n";
                html += "<div class=\"dropdown\">\n";
                html += "<a id=\"dLabel\" role=\"button\" data-toggle=\"dropdown\" data-target=\"#\" href=\"/page.html\">\n";
                html += "Job Type<span class=\"caret\"></span>\n";
                html += "  </a>\n";

                html += "<ul class=\"dropdown-menu\" role=\"menu\" aria-labelledby=\"dLabel\">\n";
                html += "<li><a href=\"#\">All</a></li>\n";
                html += "<li><a href=\"#\">Inventory Sync</a></li>\n";
                html += "<li><a href=\"#\">SCM Update</a></li>\n";
                html += "<li><a href=\"#\">Playbook Runs</a></li>\n";
                html += "</ul>\n";
                html += "</div>\n";

                html += "</div>\n"; //end of filter div

                html += "<div class=\"h6 col-xs-2 \">\n";
                html += "<div class=\"dropdown\">\n";
                html += "<a id=\"dLabel\" role=\"button\" data-toggle=\"dropdown\" data-target=\"#\" href=\"/page.html\">\n";
                html += "Period<span class=\"caret\"></span>\n";
                html += "  </a>\n";

                html += "<ul class=\"dropdown-menu\" role=\"menu\" aria-labelledby=\"dLabel\">\n";
                html += "<li><a href=\"#\">Past Day</a></li>\n";
                html += "<li><a href=\"#\">Past Week</a></li>\n";
                html += "<li><a href=\"#\">Past Month</a></li>\n";
                html += "</ul>\n";
                html += "</div>\n";
                html += "</div>\n"; //end of filter div

                html += "</div>\n"; // end of row

                html +="<div class=\"row\">\n";
                html += "<div class=\"job-status-graph\"><svg></svg></div>\n";
                html += "</div>\n";

                //
                // html += "</div>\n";

                html += "</div>\n";


                function makeJobStatusGraph(){
                    url = GetBasePath('dashboard')+'graphs/';
                    var graphData = [];

                    //d3.json("static/js/jobstatusdata.json",function(error,data) {
                    d3.json(url, function(error,data) {
                       //console.log(data);
                      graphData = [
                            {
                                "color": "#1778c3",
                                "key": "Successful",
                                "values": data.jobs.successful
                            },
                            {
                                "key" : "Failed" ,
                                "color" : "#aa0000",
                                "values": data.jobs.failed
                            }
                        ];

                        graphData.map(function(series) {
                            series.values = series.values.map(function(d) {
                                return {
                                    x: d[0],
                                    y: d[1]
                                };
                            });
                            return series;
                        });

                        nv.addGraph({
                            generate: function() {
                                var width = nv.utils.windowSize().width/3,
                                    height = nv.utils.windowSize().height/5,
                                    chart = nv.models.lineChart()
                                        .margin({top: 5, right: 75, bottom: 40, left: 85})  //Adjust chart margins to give the x-axis some breathing room.
                                        .x(function(d,i) { return i; })
                                        .useInteractiveGuideline(true)  //We want nice looking tooltips and a guideline!
                                        .transitionDuration(350)  //how fast do you want the lines to transition?
                                        .showLegend(true)       //Show the legend, allowing users to turn on/off line series.
                                        .showYAxis(true)        //Show the y-axis
                                        .showXAxis(true)        //Show the x-axis
                                        // .width(width)
                                        // .height(height)
                                        ;

                                chart.xAxis
                                    .axisLabel("Time").showMaxMin(true)
                                    .tickFormat(function(d) {
                                    var dx = graphData[0].values[d] && graphData[0].values[d].x || 0;
                                    return dx ? d3.time.format('%m/%d')(new Date(Number(dx+'000'))) : '';
                                });

                                chart.yAxis     //Chart y-axis settings
                                  .axisLabel('Jobs')
                                  .tickFormat(d3.format('.f'));

                                // d3.select('.job-status-graph svg')
                                //   .attr('width', width)
                                //   .attr('height', height)
                                //   .datum(data)
                                //   .call(chart);

                                d3.select('.job-status-graph svg')
                                        .datum(graphData).transition()
                                        .attr('width', width)
                                        .attr('height', height)
                                        .duration(500)
                                        .call(chart)
                                        .style({
                                            // 'width': width,
                                            // 'height': height,
                                    "font-family": 'Open Sans',
                                    "font-style": "normal",
                                    "font-weight":400,
                                    "src": "url(/static/fonts/OpenSans-Regular.ttf)"
                                });


                                nv.utils.windowResize(chart.update);
                                return chart;
                            },

                        });
                    });
                }


                element = angular.element(document.getElementById(target));
                element.html(html);
                $compile(element)(scope);
                makeJobStatusGraph();
                scope.$emit('WidgetLoaded');

            };
        }
    ]);