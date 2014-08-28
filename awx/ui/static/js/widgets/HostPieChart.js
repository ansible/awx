/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 */
    /**
 * @ngdoc function
 * @name widgets.function:HostPieChart
 * @description
 * HostPieChart.js
 *
 * file for the host status pie chart
 *
 */

'use strict';

angular.module('HostPieChartWidget', ['RestServices', 'Utilities'])
    .factory('HostPieChart', ['$rootScope', '$compile',
            //'Rest', 'GetBasePath', 'ProcessErrors', 'Wait',
        function ($rootScope, $compile){
            //, Rest, GetBasePath, ProcessErrors) {
            return function (params) {

                var scope = params.scope,
                    target = params.target,
                    dashboard = params.dashboard,
                    html, element, data,
                    canvas, context, winHeight, available_height, host_pie_chart;

                // html = "<div class=\"graph-container\">\n";

                html ="<div class=\"row\">\n";
                html += "<div id=\"job-status-title\" class=\"h6 col-xs-8 text-center\"><b>Host Status</b></div>\n";
                html += "</div>\n";

                html +="<div class=\"row\">\n";
                html += "<div class=\"host-pie-chart text-center\"><svg></svg></div>\n";
                html += "</div>\n";

                // html += "</div>\n";

                element = angular.element(document.getElementById(target));
                element.html(html);
                $compile(element)(scope);

                if (scope.removeResizeHostPieGraph) {
                    scope.removeResizeHostPieGraph();
                }
                scope.removeResizeHostPieGraph= scope.$on('ResizeHostPieGraph', function () {
                    if($(window).width()<500){
                        $('.graph-container').height(300);
                    }
                    else{
                        var winHeight = $(window).height(),
                        available_height = winHeight - $('#main-menu-container .navbar').outerHeight() - $('#count-container').outerHeight() - 120;
                        $('.graph-container').height(available_height/2);
                        if(host_pie_chart){
                            host_pie_chart.update();
                        }
                    }
                });

                if(dashboard.hosts.total+dashboard.hosts.failed>0){
                    data = [
                        {
                            "label": "Successful",
                            "color": "#00aa00",
                            "value" : dashboard.hosts.total
                        } ,
                        {
                            "label": "Failed",
                            "color" : "#aa0000",
                            "value" : dashboard.hosts.failed
                        }
                    ];

                    nv.addGraph(function() {
                        var width = $('.graph-container').width(), // nv.utils.windowSize().width/3,
                        height = $('.graph-container').height()*0.7; //nv.utils.windowSize().height/5,
                        host_pie_chart = nv.models.pieChart()
                          .margin({top: 5, right: 75, bottom: 40, left: 85})
                          .x(function(d) { return d.label; })
                          .y(function(d) { return d.value; })
                          .showLabels(true)
                          .labelThreshold(0.01)
                          .tooltipContent(function(x, y) {
                                return '<b>'+x+'</b>'+ '<p>' +  Math.floor(y) + ' Hosts ' +  '</p>';
                            })
                          .color(['#00aa00', '#aa0000']);

                        host_pie_chart.pie.pieLabelsOutside(true).labelType("percent");

                        d3.select(".host-pie-chart svg")
                            .datum(data)
                            .attr('width', width)
                            .attr('height', height)
                            .transition().duration(350)
                            .call(host_pie_chart)
                             .style({
                            "font-family": 'Open Sans',
                            "font-style": "normal",
                            "font-weight":400,
                            "src": "url(/static/fonts/OpenSans-Regular.ttf)"
                        });
                        // nv.utils.windowResize(host_pie_chart.update);
                        scope.$emit('WidgetLoaded');
                        return host_pie_chart;
                    });
                }
                else{
                    winHeight = $(window).height();
                    available_height = winHeight - $('#main-menu-container .navbar').outerHeight() - $('#count-container').outerHeight() - 120;
                    $('.graph-container:eq(1)').height(available_height/2);
                    $('.host-pie-chart svg').replaceWith('<canvas id="circlecanvas" width="120" height="120"></canvas>');

                    canvas = document.getElementById("circlecanvas");
                    context = canvas.getContext("2d");
                    context.arc(55, 55, 50, 0, Math.PI * 2, false);
                    context.lineWidth = 1;
                    context.strokeStyle = '#1778c3';
                    context.stroke();
                    context.font = "12px Open Sans";
                    context.fillText("No Host data",18,55);

                    scope.$emit('WidgetLoaded');
                }
            };
        }
    ]);
