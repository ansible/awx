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
    .factory('HostGraph', ['$rootScope', '$compile', '$location', 'Rest', 'GetBasePath', 'ProcessErrors', 'Wait',
        function ($rootScope, $compile,  $location, Rest, GetBasePath, ProcessErrors) {
            return function (params) {

                var scope = params.scope,
                    target = params.target,
                    html, element, url, license;


               // html = "<div class=\"graph-container\">\n";
                html ="<div class=\"row\">\n";
                html += "<div class=\"h6 col-xs-8 text-center\"><b>Host Count</b></div>\n";
                html += "</div>\n";
                html +="<div class=\"row\">\n";
                html += "<div class=\"host-count-graph\"><svg></svg></div>\n";

               // html += "</div>\n";



                element = angular.element(document.getElementById(target));
                element.html(html);
                $compile(element)(scope);

                url = GetBasePath('config');

                Rest.setUrl(url);
                Rest.get()
                    .success(function (data){
                        license = data.license_info.instance_count;
                        scope.$emit('licenseCountReady', license);
                    })
                    .error(function (data, status) {
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                            msg: 'Failed to get: ' + url + ' GET returned: ' + status });
                    });

                if (scope.removeLicenseCountReady) {
                    scope.removeLicenseCountReady();
                }
                scope.removeLicenseCountReady = scope.$on('licenseCountReady', function (e, license) {
                    url = GetBasePath('dashboard')+'graphs/inventory/';
                    Rest.setUrl(url);
                    Rest.get()
                        .success(function (data) {
                            scope.$emit('hostDataReady', data, license);
                        })
                        .error(function (data, status) {
                            ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                                msg: 'Failed to get: ' + url + ' GET returned: ' + status });
                        });

                });

                if (scope.removeHostDataReady) {
                    scope.removeHostDataReady();
                }
                scope.removeHostDataReady = scope.$on('hostDataReady', function (e, data, license) {

                        //url = GetBasePath('dashboard')+'graphs/';
                        var graphData = [
                                {
                                    "key" : "Hosts" ,
                                    "color" : "#1778c3",
                                    "values": data.hosts
                                },
                                {
                                    "key" : "License" ,
                                    "color" : "#171717",
                                    "values": data.hosts
                                }
                            ];

                        graphData.map(function(series) {
                                if(series.key==="Hosts"){
                                    series.values = series.values.map(function(d) {
                                        return {
                                            x: d[0],
                                            y: d[1]
                                        };
                                    });
                                }
                                if(series.key==="License"){
                                    series.values = series.values.map(function(d) {
                                        return {
                                            x: d[0],
                                            y: license
                                        };
                                    });

                                }
                                return series;

                            });

                        nv.addGraph({
                                generate: function() {
                                    var width = $('.graph-container').width(), // nv.utils.windowSize().width/3,
                                    height = $('.graph-container').height()*0.6, //nv.utils.windowSize().height/5,
                                    chart = nv.models.lineChart()
                                        .margin({top: 15, right: 75, bottom: 40, left: 85})
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
                                        var dx = graphData[0].values[d] && graphData[0].values[d].x || 0;
                                        return dx ? d3.time.format('%m/%d')(new Date(Number(dx+'000'))) : '';
                                    });

                                    chart.yAxis     //Chart y-axis settings
                                    .axisLabel('Hosts')
                                    .tickFormat(d3.format('.f'));

                                    d3.select('.host-count-graph svg')
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

                                    // d3.selectAll(".nv-line").on("click", function () {
                                    //     alert("clicked");
                                    // });

                                    nv.utils.windowResize(chart.update);

                                    return chart;

                                },

                            });
                        //});
                    });



            };
        }
    ]);