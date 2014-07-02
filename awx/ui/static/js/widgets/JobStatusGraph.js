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
    .factory('JobStatusGraph', ['$rootScope', '$compile', 'Rest', 'GetBasePath', 'ProcessErrors', 'Wait',
        function ($rootScope, $compile) {
            return function (params) {

                var scope = params.scope,
                    target = params.target,
                    //dashboard = params.dashboard,

                    html, element;

                html = "<div class=\"graph-container\">\n";
                        html +="<div class=\"row\">\n";
                                html += "<div class=\"h6 col-lg-12 text-center\">Job Status</div>\n";
                                 html += "<div class=\"job-status-graph\"><svg></svg></div>\n";
                        html += "</div>\n";
                html += "</div>\n";


                function makeJobStatusGraph(){
                    d3.json("static/js/jobstatusdata.json",function(error,data) {

                        data.map(function(series) {
                            series.values = series.values.map(function(d) { return {x: d[0], y: d[1] }; });
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
                                    .axisLabel("Tme").showMaxMin(true)
                                    .tickFormat(function(d) {
                                    var dx = data[0].values[d] && data[0].values[d].x || 0;
                                    return dx ? d3.time.format('%m/%d')(new Date(dx)) : '';
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