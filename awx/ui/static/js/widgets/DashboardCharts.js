/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 * Dashboard.js
 *
 * The new dashboard
 *
 */

'use strict';

angular.module('DashboardChartsWidget', ['RestServices', 'Utilities'])
    .factory('DashboardCharts', ['$rootScope', '$compile', 'Rest', 'GetBasePath', 'ProcessErrors', 'Wait',
        function ($rootScope, $compile) {
            return function (params) {

                var scope = params.scope,
                    target = params.target,
                    //dashboard = params.dashboard,

                    html, element;

                html = "<div class=\"panel panel-default\" style=\"border:none\">\n";
                html += "<div class=\"panel-body \">\n";

                html += "<table class=\"table\">\n";
                html += "<tr>\n";
                html += "<td class=\"h5 col-lg-6 text-center\" style=\"border:none\">Job Status Graph</td>\n";
                html += "<td class=\"h5 col-lg-6 text-center\" style=\"border:none\">Hosts</td>\n";
                html += "</tr>\n";
                html += "<tr>\n";
                html += "<td class=\"job-status-graph\" style=\"border:none\"><svg></svg></td>\n";
                html += "<td class=\"host-count-graph\" style=\"border:none\"><svg></svg></td>\n";
                html += "</tr>\n";
                html += "</table>\n";


                function makeJobStatusGraph(){
                    d3.json("static/js/jobstatusdata.json",function(error,data) {

                        data.map(function(series) {
                            series.values = series.values.map(function(d) { return {x: d[0], y: d[1] }; });
                            return series;
                        });

                        nv.addGraph({
                            generate: function() {
                                var width = nv.utils.windowSize().width - 40,
                                    height = nv.utils.windowSize().height - 40,
                                    chart = nv.models.lineChart()
                                        // .margin({top: 20, right: 80, bottom: 50, left: 50})  //Adjust chart margins to give the x-axis some breathing room.
                                        .x(function(d,i) { return i; })
                                        .useInteractiveGuideline(true)  //We want nice looking tooltips and a guideline!
                                        .transitionDuration(350)  //how fast do you want the lines to transition?
                                        .showLegend(true)       //Show the legend, allowing users to turn on/off line series.
                                        .showYAxis(true)        //Show the y-axis
                                        .showXAxis(true)        //Show the x-axis
                                        ;

                                chart.xAxis
                                    .axisLabel("time")
                                    .tickFormat(function(d) {
                                    var dx = data[0].values[d] && data[0].values[d].x || 0;
                                    return dx ? d3.time.format('%x')(new Date(dx)) : '';
                                });

                                chart.yAxis     //Chart y-axis settings
                                  .axisLabel('Jobs')
                                  .tickFormat(d3.format('.f'));

                                d3.select('.job-status-graph svg')
                                  .attr('width', width)
                                  .attr('height', height)
                                  .datum(data)
                                  .call(chart);

                                return chart;
                            },
                              // callback: function(graph) {
                              //   window.onresize = function() {
                              //     var width = nv.utils.windowSize().width - 40,
                              //         height = nv.utils.windowSize().height - 40,
                              //         margin = graph.margin();


                              //     if (width < margin.left + margin.right + 20)
                              //       width = margin.left + margin.right + 20;

                              //     if (height < margin.top + margin.bottom + 20)
                              //       height = margin.top + margin.bottom + 20;


                              //     graph
                              //        .width(width)
                              //        .height(height);

                              //     d3.select('.job-status-graph svg')
                              //       .attr('width', width)
                              //       .attr('height', height)
                              //       .call(graph);
                              //   };
                              // }
                        });
                    });
                }

                function makeHostCountGraph(){
                    d3.json("static/js/hostcount.json",function(error,data) {

                        data.map(function(series) {
                            series.values = series.values.map(function(d) { return {x: d[0], y: d[1] }; });
                            return series;
                        });

                        nv.addGraph({
                            generate: function() {
                                var width = nv.utils.windowSize().width - 40,
                                    height = nv.utils.windowSize().height - 40,
                                    chart = nv.models.lineChart()
                                        // .margin({top: 20, right: 80, bottom: 50, left: 50})  //Adjust chart margins to give the x-axis some breathing room.
                                        .x(function(d,i) { return i ;})
                                        .useInteractiveGuideline(true)  //We want nice looking tooltips and a guideline!
                                        .transitionDuration(350)  //how fast do you want the lines to transition?
                                        .showLegend(true)       //Show the legend, allowing users to turn on/off line series.
                                        .showYAxis(true)        //Show the y-axis
                                        .showXAxis(true)        //Show the x-axis
                                        ;

                                chart.xAxis
                                    .axisLabel("time")
                                    .tickFormat(function(d) {
                                    var dx = data[0].values[d] && data[0].values[d].x || 0;
                                    return dx ? d3.time.format('%x')(new Date(dx)) : '';
                                });

                                chart.yAxis     //Chart y-axis settings
                                  .axisLabel('Jobs')
                                  .tickFormat(d3.format('.f'));

                                d3.select('.host-count-graph svg')
                                  .attr('width', width)
                                  .attr('height', height)
                                  .datum(data)
                                  .call(chart);

                                return chart;
                            },
                              // callback: function(graph) {
                              //   window.onresize = function() {
                              //     var width = nv.utils.windowSize().width - 40,
                              //         height = nv.utils.windowSize().height - 40,
                              //         margin = graph.margin();


                              //     if (width < margin.left + margin.right + 20)
                              //       width = margin.left + margin.right + 20;

                              //     if (height < margin.top + margin.bottom + 20)
                              //       height = margin.top + margin.bottom + 20;


                              //     graph
                              //        .width(width)
                              //        .height(height);

                              //     d3.select('.job-status-graph svg')
                              //       .attr('width', width)
                              //       .attr('height', height)
                              //       .call(graph);
                              //   };
                              // }
                        });
                    });
                }
                        // var chart = nv.models.lineChart()
                        //                 // .margin({top: 20, right: 80, bottom: 50, left: 50})  //Adjust chart margins to give the x-axis some breathing room.
                        //                 .x(function(d,i) { return i })
                        //                 .useInteractiveGuideline(true)  //We want nice looking tooltips and a guideline!
                        //                 .transitionDuration(350)  //how fast do you want the lines to transition?
                        //                 .showLegend(true)       //Show the legend, allowing users to turn on/off line series.
                        //                 .showYAxis(true)        //Show the y-axis
                        //                 .showXAxis(true)        //Show the x-axis
                        //   ;

                        // chart.width(($(window).width())/3);
                        // chart.height(($(window).height())/3);
                        //   chart.xAxis
                        //         .axisLabel("time")
                        //         .tickFormat(function(d) {
                        //         var dx = data[0].values[d] && data[0].values[d].x || 0;
                        //         return dx ? d3.time.format('%x')(new Date(dx)) : '';
                        //     });

                        //   chart.yAxis     //Chart y-axis settings
                        //       .axisLabel('Jobs')
                        //       .tickFormat(d3.format('.f'));

                        //   /* Done setting the chart up? Time to render it!*/
                        //   //var myData = sinAndCos();   //You need data...

                        //   d3.select('.job-status-graph svg')    //Select the <svg> element you want to render the chart in.
                        //       .datum(data)         //Populate the <svg> element with chart data...
                        //       .call(chart);          //Finally, render the chart!

                        //   //Update the chart when window resizes.
                        //   nv.utils.windowResize(function() { chart.update() });
                        //   return chart;
                      // });

                   // });

                // };




                element = angular.element(document.getElementById(target));
                element.html(html);
                $compile(element)(scope);
                makeJobStatusGraph();
                makeHostCountGraph();
                scope.$emit('WidgetLoaded');

            };
        }
    ]);