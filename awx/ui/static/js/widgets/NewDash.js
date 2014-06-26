/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 * Dashboard.js
 *
 * The new dashboard
 *
 */

'use strict';

angular.module('NewDashWidget', ['RestServices', 'Utilities'])
    .factory('NewDash', ['$rootScope', '$compile', 'Rest', 'GetBasePath', 'ProcessErrors', 'Wait',
        function ($rootScope, $compile) {
            return function (params) {

                var scope = params.scope,
                    target = params.target,
                    dashboard = params.dashboard,

                    html, element;

                html = "<div id=\"dashcontainer\" class=\"panel panel-default\">\n";
                html += "<div class=\"panel-heading\">New Dashboard</div>\n";
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

                html += "<br>\n";
                html += "<hr>\n";
                html += "<table class=\"table\">\n";
                html += "<tr>\n";
                html += "<td class=\"h5 col-lg-6 text-center\" style=\"border:none\">Job Status Graph</td>\n";
                html += "<td class=\"h5 col-lg-6 text-center\" style=\"border:none\">Hosts</td>\n";
                html += "</tr>\n";
                html += "<tr>\n";
                //html += "<td id=\"job-status-graph-container\" style=\"border:none\">\n";
                html += "<td class=\"job-status-graph\" style=\"border:none\"><svg></svg></td>\n";
                // //class=\"job-status-graph col-lg-6\" style=\"border:none\">\n";
               // html += "<svg class=\"job-status-graph\" width=\"500\" height=\"200\" viewBox=\"0 0 500 200\" perserveAspectRatio=\"xMidYMid\"></td>\n";
                html += "<td class=\"host-count-graph\" style=\"border:none\"></td>\n";
                //<svg class=\"host-count-graph\" width=\"500\" height=\"200\" viewBox=\"0 0 500 200\" perserveAspectRatio=\"xMidYMid\"></td>\n";
                // html += "<td class=\"host-count-graph col-lg-6\" style=\"border:none\"></td>\n";
                html += "</tr>\n";
                html += "</table>\n";

                // html += "<br>\n";
                // html += "<hr>\n";
                html += "<table class=\"table table-bordered\">\n";
                html += "<tr>\n";
                html += "<td class=\"h5 col-lg-6 text-center\">Active Jobs</td>\n";
                html += "<td class=\"h5 col-lg-6 text-center\">Remaining licenses</td>\n";
                html += "</tr>\n";
                html += "<tr>\n";
                html += "<td class=\"col-lg-8\">\n";

//---------------------------------------------------------------------------------------------------------

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
                html += "<td class=\"col-lg-4 text-center\">Your license will out in <br><u> 365 </u> days</td>\n";
                html += "</tr>\n";
                html += "</table>\n";

                html += "</div>\n";
                html += "</div>\n";
                html += "</div>\n";

               // var graphWidth = ($(window).width())/3;
                // var graphHeight = ($(window).height())/3;

                //function makeGraph(){
                 //   d3.json("static/js/jobstatusdata.json",function(error,data) {
                      // nv.addGraph(function() {
                      //     var chart = nv.models.lineChart()
                      //       .margin({left: 100})  //Adjust chart margins to give the x-axis some breathing room.
                      //       .useInteractiveGuideline(true)  //We want nice looking tooltips and a guideline!
                      //       .transitionDuration(350)  //how fast do you want the lines to transition?
                      //       .showLegend(true)       //Show the legend, allowing users to turn on/off line series.
                      //       .showYAxis(true)        //Show the y-axis
                      //       .showXAxis(true)        //Show the x-axis

                      //     chart.xAxis.tickFormat(function(d) {
                      //       var dx = data[0].values[d] && data[0].values[d][0] || 0;
                      //       return d3.time.format('%x')(new Date(dx))
                      //     });

                      //     chart.y1Axis
                      //         .tickFormat(d3.format(',f'));

                      //     chart.y2Axis
                      //         .tickFormat(function(d) { return '$' + d3.format(',f')(d) });

                      //     chart.bars.forceY([0]);

                      //     d3.select('.job-status-graph svg')
                      //      .datum(data)
                      //       .transition()
                      //       .duration(0)
                      //       .call(chart);

                      //     nv.utils.windowResize(chart.update);

                      //     return chart;
                      // });
                //         var chart = nv.models.lineChart()
                //                         .margin({left: 100})  //Adjust chart margins to give the x-axis some breathing room.
                //                         .useInteractiveGuideline(true)  //We want nice looking tooltips and a guideline!
                //                         .transitionDuration(350)  //how fast do you want the lines to transition?
                //                         .showLegend(true)       //Show the legend, allowing users to turn on/off line series.
                //                         .showYAxis(true)        //Show the y-axis
                //                         .showXAxis(true)        //Show the x-axis
                //           ;

                //           chart.xAxis     //Chart x-axis settings
                //               .axisLabel('Time (ms)')
                //               .tickFormat(d3.format(',r'));

                //           chart.yAxis     //Chart y-axis settings
                //               .axisLabel('Voltage (v)')
                //               .tickFormat(d3.format('.02f'));

                //           /* Done setting the chart up? Time to render it!*/
                //           //var myData = sinAndCos();   //You need data...

                //           d3.select('.job-status-graph svg')    //Select the <svg> element you want to render the chart in.
                //               .datum(data)         //Populate the <svg> element with chart data...
                //               .call(chart);          //Finally, render the chart!

                //           //Update the chart when window resizes.
                //           nv.utils.windowResize(function() { chart.update() });
                //           return chart;
                //         });

                //     });

                // };


                // function makeJobStatusGraph(){
                     // Adjust the size
        // width = $('#job-summary-container .job_well').width();
        // height = $('#job-summary-container .job_well').height() - $('#summary-well-top-section').height() - $('#graph-section .header').outerHeight() - 15;
        // svg_radius = Math.min(width, height);
        // svg_width = width;
        // svg_height = height;
        // if (svg_height > 0 && svg_width > 0) {
        //     if (!resize && $('#graph-section svg').length > 0) {
        //         Donut3D.transition("completedHostsDonut", graph_data, Math.floor(svg_radius * 0.50), Math.floor(svg_radius * 0.25), 18, 0.4);
        //     }
        //     else {
        //         if ($('#graph-section svg').length > 0) {
        //             $('#graph-section svg').remove();
        //         }
        //         svg = d3.select("#graph-section").append("svg").attr("width", svg_width).attr("height", svg_height);
        //         svg.append("g").attr("id","completedHostsDonut");
        //         Donut3D.draw("completedHostsDonut", graph_data, Math.floor(svg_width / 2), Math.floor(svg_height / 2), Math.floor(svg_radius * 0.50), Math.floor(svg_radius * 0.25), 18, 0.4);
        //         $('#graph-section .header .legend').show();
        //     }
        // }


                //     var margin = {top: 20, right: 80, bottom: 30, left: 50},
                //         width = graphWidth - margin.left - margin.right,
                //         height = graphHeight - margin.top - margin.bottom;

                //     var parseDate = d3.time.format("%Y%m%d").parse;

                //     var x = d3.time.scale()
                //         .range([0, width]);

                //     var y = d3.scale.linear()
                //         .range([height, 0]);

                //     var color = d3.scale.category10();

                //     var xAxis = d3.svg.axis()
                //         .scale(x)
                //         .orient("bottom");

                //     var yAxis = d3.svg.axis()
                //         .scale(y)
                //         .orient("left");

                //     var line = d3.svg.line()
                //         .interpolate("basis")
                //         .x(function(d) { return x(d.date); })
                //         .y(function(d) { return y(d.hostCount); });

                //     var svg = d3.select(".job-status-graph").append("svg")
                //         .attr("width", width + margin.left + margin.right)
                //         .attr("height", height + margin.top + margin.bottom)
                //       .append("g")
                //         .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

                //     d3.json("static/js/jobstatusdata.json", function(error, data) {
                //       color.domain(d3.keys(data[0]).filter(function(key) { return key !== "date"; }));

                //       data.forEach(function(d) {
                //         d.date = parseDate(d.date);
                //       });

                //       var status = color.domain().map(function(name) {
                //         return {
                //           name: name,
                //           values: data.map(function(d) {
                //             return {date: d.date, hostCount: +d[name]};
                //           })
                //         };
                //       });

                //       x.domain(d3.extent(data, function(d) { return d.date; }));

                //       y.domain([
                //         d3.min(status, function(c) { return d3.min(c.values, function(v) { return v.hostCount; }); }),
                //         d3.max(status, function(c) { return d3.max(c.values, function(v) { return v.hostCount; }); })
                //       ]);

                //       svg.append("g")
                //           .attr("class", "x axis")
                //           .attr("transform", "translate(0," + height + ")")
                //           .call(xAxis);

                //       svg.append("g")
                //           .attr("class", "y axis")
                //           .call(yAxis)
                //         .append("text")
                //           .attr("transform", "rotate(-90)")
                //           .attr("y", 6)
                //           .attr("dy", ".71em")
                //           .style("text-anchor", "end")
                //           .text("Number of hosts");

                //       var series = svg.selectAll(".series")
                //           .data(status)
                //         .enter().append("g")
                //           .attr("class", "series");

                //       series.append("path")
                //           .attr("class", "line")
                //           .attr("d", function(d) { return line(d.values); })
                //           .style("stroke", function(d) { return color(d.name); });

                //       series.append("text")
                //           .datum(function(d) { return {name: d.name, value: d.values[d.values.length - 1]}; })
                //           .attr("transform", function(d) { return "translate(" + x(d.value.date) + "," + y(d.value.hostCount) + ")"; })
                //           .attr("x", 3)
                //           .attr("dy", ".35em")
                //           .text(function(d) { return d.name; });
                //     });

                // };

                // function makeHostCountGraph(){
                //     var margin = {top: 20, right: 80, bottom: 30, left: 50},
                //         width = graphWidth - margin.left - margin.right,
                //         height = graphHeight - margin.top - margin.bottom;

                //     var parseDate = d3.time.format("%Y%m%d").parse;

                //     var x = d3.time.scale()
                //         .range([0, width]);

                //     var y = d3.scale.linear()
                //         .range([height, 0]);

                //     var color = d3.scale.category10();

                //     var xAxis = d3.svg.axis()
                //         .scale(x)
                //         .orient("bottom");

                //     var yAxis = d3.svg.axis()
                //         .scale(y)
                //         .orient("left");

                //     var line = d3.svg.line()
                //         .interpolate("basis")
                //         .x(function(d) { return x(d.date); })
                //         .y(function(d) { return y(d.hostCount); });

                //     var svg = d3.select(".host-count-graph").append("svg")
                //         .attr("width", width + margin.left + margin.right)
                //         .attr("height", height + margin.top + margin.bottom)
                //       .append("g")
                //         .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

                //     d3.json("static/js/hostcount.json", function(error, data) {
                //       color.domain(d3.keys(data[0]).filter(function(key) { return key !== "date"; }));

                //       data.forEach(function(d) {
                //         d.date = parseDate(d.date);
                //       });

                //       var status = color.domain().map(function(name) {
                //         return {
                //           name: name,
                //           values: data.map(function(d) {
                //             return {date: d.date, hostCount: +d[name]};
                //           })
                //         };
                //       });

                //       x.domain(d3.extent(data, function(d) { return d.date; }));

                //       y.domain([
                //         d3.min(status, function(c) { return d3.min(c.values, function(v) { return v.hostCount; }); }),
                //         d3.max(status, function(c) { return d3.max(c.values, function(v) { return v.hostCount; }); })
                //       ]);

                //       svg.append("g")
                //           .attr("class", "x axis")
                //           .attr("transform", "translate(0," + height + ")")
                //           .call(xAxis);

                //       svg.append("g")
                //           .attr("class", "y axis")
                //           .call(yAxis)
                //         .append("text")
                //           .attr("transform", "rotate(-90)")
                //           .attr("y", 6)
                //           .attr("dy", ".71em")
                //           .style("text-anchor", "end")
                //           .text("Number of hosts");

                //       var series = svg.selectAll(".series")
                //           .data(status)
                //         .enter().append("g")
                //           .attr("class", "series");

                //       series.append("path")
                //           .attr("class", "line")
                //           .attr("d", function(d) { return line(d.values); })
                //           .style("stroke", function(d) { return color(d.name); });

                //       series.append("text")
                //           .datum(function(d) { return {name: d.name, value: d.values[d.values.length - 1]}; })
                //           .attr("transform", function(d) { return "translate(" + x(d.value.date) + "," + y(d.value.hostCount) + ")"; })
                //           .attr("x", 3)
                //           .attr("dy", ".35em")
                //           .text(function(d) { return d.name; });
                //     });

                // };



                element = angular.element(document.getElementById(target));
                element.html(html);
                $compile(element)(scope);
                // makeGraph();
                // makeJobStatusGraph();
                // makeHostCountGraph();
                scope.$emit('WidgetLoaded');

            };
        }
    ]);