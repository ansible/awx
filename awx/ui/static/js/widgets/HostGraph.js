/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 * Dashboard.js
 *
 * The new dashboard
 *
 */

'use strict';

angular.module('HostGraphWidget', ['RestServices', 'Utilities'])
    .factory('HostGraph', ['$rootScope', '$compile', 'Rest', 'GetBasePath', 'ProcessErrors', 'Wait',
        function ($rootScope, $compile) {
            return function (params) {

                var scope = params.scope,
                    target = params.target,
                    //dashboard = params.dashboard,

                    html, element;

                // html = "<div class=\"panel panel-default\" style=\"border:none\">\n";
                html = "<div id=\"graph-container\" class=\"panel-body \" style=\"border:none\">\n";

                html += "<table class=\"table\" >\n";
                html += "<tr> \n";
                // html += "<td class=\"h5 col-lg-6 text-center\" style=\"border:none\">Job Status</td>\n";
                html += "<td class=\"h6 text-center\" style=\"border:none\">Hosts vs License Agreement</td>\n";
                html += "</tr>\n";
                html += "<tr>\n";
                // html += "<td class=\"job-status-graph\" style=\"border:none\"><svg></svg></td>\n";
                html += "<td class=\"host-count-graph\" style=\"border:none\"><svg></svg></td>\n";
                html += "</tr>\n";
                html += "</table>\n";
                html += "</div>\n";
                // html += "</div>\n";



                function makeHostCountGraph(){
                    d3.json("static/js/hostcount.json",function(error,data) {

                        data.map(function(series) {
                            series.values = series.values.map(function(d) { return {x: d[0], y: d[1] }; });
                            return series;
                        });

                        nv.addGraph({
                            generate: function() {
                                    var width = nv.utils.windowSize().width/3,
                                    height = nv.utils.windowSize().height/4,
                                    chart = nv.models.lineChart()
                                        .margin({top: 15, right: 75, bottom: 40, left: 80})
                                        .x(function(d,i) { return i ;})
                                        .useInteractiveGuideline(true)  //We want nice looking tooltips and a guideline!
                                        .transitionDuration(350)  //how fast do you want the lines to transition?
                                        .showLegend(true)       //Show the legend, allowing users to turn on/off line series.
                                        .showYAxis(true)        //Show the y-axis
                                        .showXAxis(true)        //Show the x-axis
                                        ;

                                    chart.xAxis
                                    .axisLabel("Time")
                                    .tickFormat(function(d) {
                                        var dx = data[0].values[d] && data[0].values[d].x || 0;
                                        return dx ? d3.time.format('%m/%d')(new Date(dx)) : '';
                                    });

                                    chart.yAxis     //Chart y-axis settings
                                    .axisLabel('Hosts')
                                    .tickFormat(d3.format('.f'));

                                    d3.select('.host-count-graph svg')
                                    .datum(data).transition()
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

                                    d3.selectAll(".nv-line").on("click", function () {
                                        alert("clicked");
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
                // makeJobStatusGraph();
                makeHostCountGraph();
                scope.$emit('WidgetLoaded');

            };
        }
    ]);