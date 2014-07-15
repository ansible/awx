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
        function ($rootScope, $compile , $location, Rest, GetBasePath, ProcessErrors) {
            return function (params) {

                var scope = params.scope,
                    target = params.target,
                    // dashboard = params.dashboard,
                    html, element, url,
                    period="month",
                    job_type="all";

                // html = "<div class=\"graph-container\">\n";

                html = "<div class=\"row\">\n";
                html += "<div id=\"job-status-title\" class=\"h6 col-xs-8 text-center\"><b>Job Status</b></div>\n";  // for All Jobs, Past Month

                html += "<div class=\"h6 col-xs-2 \">\n";
                html += "<div class=\"dropdown\">\n";
                html += "<a id=\"type-dropdown\" role=\"button\" data-toggle=\"dropdown\" data-target=\"#\" href=\"/page.html\">\n";
                html += "Job Type<span class=\"caret\"></span>\n";
                html += "  </a>\n";

                html += "<ul class=\"dropdown-menu\" role=\"menu\" aria-labelledby=\"type-dropdown\">\n";
                html += "<li><a class=\"m\" id=\"all\">All</a></li>\n";
                html += "<li><a class=\"m\" id=\"inv_sync\">Inventory Sync</a></li>\n";
                html += "<li><a class=\"m\" id=\"scm_update\">SCM Update</a></li>\n";
                html += "<li><a class=\"m\" id=\"playbook_run\">Playbook Run</a></li>\n";
                html += "</ul>\n";
                html += "</div>\n";

                html += "</div>\n"; //end of filter div

                html += "<div class=\"h6 col-xs-2 \">\n";
                html += "<div class=\"dropdown\">\n";
                html += "<a id=\"period-dropdown\" role=\"button\" data-toggle=\"dropdown\" data-target=\"#\" href=\"/page.html\">\n";
                html += "Period<span class=\"caret\"></span>\n";
                html += "  </a>\n";

                html += "<ul class=\"dropdown-menu\" role=\"menu\" aria-labelledby=\"period-dropdown\">\n";
                html += "<li><a class=\"n\" id=\"day\" >Past 24 Hours </a></li>\n";
                html += "<li><a class=\"n\" id=\"week\">Past Week</a></li>\n";
                html += "<li><a class=\"n\" id=\"month\">Past Month</a></li>\n";
                html += "</ul>\n";
                html += "</div>\n";
                html += "</div>\n"; //end of filter div

                html += "</div>\n"; // end of row

                html +="<div class=\"row\">\n";
                html += "<div class=\"job-status-graph\"><svg></svg></div>\n";
                html += "</div>\n";

                // html += "</div>\n";

                function createGraph(){

                    url = GetBasePath('dashboard')+'graphs/jobs/?period='+period+'&job_type='+job_type;
                    Rest.setUrl(url);
                    Rest.get()
                        .success(function (data){
                            scope.$emit('graphDataReady', data);
                            return job_type, period;

                        })
                        .error(function (data, status) {
                            ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                                msg: 'Failed to get: ' + url + ' GET returned: ' + status });
                        });
                }

                element = angular.element(document.getElementById(target));
                element.html(html);
                $compile(element)(scope);

                createGraph();


                if (scope.removeGraphDataReady) {
                    scope.removeGraphDataReady();
                }
                scope.removeGraphDataReady = scope.$on('graphDataReady', function (e, data) {


                    var timeFormat, graphData = [
                        {
                            "color": "#00aa00",
                            "key": "Successful",
                            "values": data.jobs.successful
                        },
                        {
                            "key" : "Failed" ,
                            "color" : "#aa0000",
                            "values": data.jobs.failed
                        }
                    ];

                    if(period==="day"){
                        timeFormat="%H:%M";
                    }
                    else {
                        timeFormat = '%m/%d';
                    }
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
                                    var width = $('.graph-container').width(), // nv.utils.windowSize().width/3,
                                        height = $('.graph-container').height()*0.8, //nv.utils.windowSize().height/5,
                                        chart = nv.models.lineChart()
                                           .margin({top: 5, right: 75, bottom: 40, left: 85})  //Adjust chart margins to give the x-axis some breathing room.
                                            .x(function(d,i) { return i; })
                                            .useInteractiveGuideline(true)  //We want nice looking tooltips and a guideline!
                                            .transitionDuration(350)  //how fast do you want the lines to transition?
                                            .showLegend(true)       //Show the legend, allowing users to turn on/off line series.
                                            .showYAxis(true)        //Show the y-axis
                                            .showXAxis(true)        //Show the x-axis
                                            //  .width(width)
                                            // .height(height)
                                            ;

                                    chart.xAxis
                                        .axisLabel("Time").showMaxMin(true)
                                        .tickFormat(function(d) {
                                        var dx = graphData[0].values[d] && graphData[0].values[d].x || 0;
                                        return dx ? d3.time.format(timeFormat)(new Date(Number(dx+'000'))) : '';
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

                                    nv.utils.windowResize(function(){
                                        if($(window).width()<500){
                                            $('.graph-container').height(300);
                                        }
                                        else{
                                            var winHeight = $(window).height(),
                                            available_height = winHeight - $('#main-menu-container .navbar').outerHeight() - $('#count-container').outerHeight() - 93;
                                            $('.graph-container').height(available_height/2);
                                            chart.update();
                                        }
                                    });
                                    // nv.utils.windowResize(chart.update);


                                    //On click, update with new data
                                    d3.selectAll(".n")
                                        .on("click", function() {
                                            period = this.getAttribute("id");
                                            $('#period-dropdown').replaceWith("<a id=\"period-dropdown\" role=\"button\" data-toggle=\"dropdown\" data-target=\"#\" href=\"/page.html\">"+this.text+"<span class=\"caret\"><span>\n");
                                            //$('#period-dropdown').text(this.text);
                                            // var title = $('#job-status-title').text(),
                                            // str = title.slice(0,title.search(","))+", "+this.innerHTML;
                                            // $('#job-status-title').html("<b>"+str+" </b>");
                                            createGraph();
                                        });

                                         //On click, update with new data
                                    d3.selectAll(".m")
                                        .on("click", function() {
                                            job_type = this.getAttribute("id");
                                            $('#type-dropdown').replaceWith("<a id=\"type-dropdown\" role=\"button\" data-toggle=\"dropdown\" data-target=\"#\" href=\"/page.html\">"+this.text+"<span class=\"caret\"><span>\n");
                                            // var title = $('#job-status-title').text(),
                                            // str = title.slice(title.search(","));
                                            // $('#job-status-title').html("<b>Job Status for "+this.innerHTML+" Jobs"+str+" </b>");
                                            createGraph();
                                        });

                                    scope.$emit('WidgetLoaded');
                                    return chart;

                                },


                    });

                });

            };
        }
    ]);