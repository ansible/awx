/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default
    [   '$rootScope',
        '$compile',
        '$location' ,
        '$window',
        'Wait',
        'adjustGraphSize',
        'jobStatusGraphData',
        'templateUrl',
        JobStatusGraph
    ];

function JobStatusGraph($rootScope, $compile , $location, $window, Wait, adjustGraphSize, graphDataService, templateUrl) {
            return {
                restrict: 'E',
                scope: {
                    data: '='
                },
                templateUrl: templateUrl('dashboard/graphs/job-status/job_status_graph'),
                link: link
            };

            function link(scope, element) {
                var job_type, job_status_chart = nv.models.lineChart();

                scope.period="month";
                scope.jobType="all";

                scope.$watch('data', function(value) {
                    if (value) {
                        createGraph(scope.period, scope.jobType, value, scope.status);
                    }
                }, true);

                function recreateGraph(period, jobType, status) {
                    graphDataService.get(period, jobType, status)
                        .then(function(data) {
                            scope.data = data;
                            scope.period = period;
                            scope.jobType = jobType;
                            scope.status = status;
                        });
                }

                scope.$on('jobStatusChange', function(event, status){
                    recreateGraph(scope.period, scope.jobType, status);
                });

                function createGraph(period, jobtype, data, status){
                    scope.period = period;
                    scope.jobType = jobtype;
                    scope.status = status;

                    var timeFormat, graphData = [
                        {   "color": "#3CB878",
                            "key": "SUCCESSFUL",
                            "values": data.jobs.successful
                        },
                        {   "key" : "FAILED" ,
                            "color" : "#ff5850",
                            "values": data.jobs.failed
                        }
                    ];

                    graphData = _.reject(graphData, function(num){
                        if(status!== undefined && status === num.key.toLowerCase()){
                            return num;
                        }
                    });

                    if(period==="day") {
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

                    job_status_chart
                    .x(function(d,i) { return i; })
                    .useInteractiveGuideline(true)  //We want nice looking tooltips and a guideline!
                    .showLegend(false)       //Show the legend, allowing users to turn on/off line series.
                    .showYAxis(true)        //Show the y-axis
                    .showXAxis(true);       //Show the x-axis

                    job_status_chart.interactiveLayer.tooltip.fixedTop(-10); //distance from the top of the chart to tooltip
                    job_status_chart.interactiveLayer.tooltip.distance(-1); //distance from interactive line to tooltip

                    job_status_chart.xAxis
                    .axisLabel("TIME")//.showMaxMin(true)
                    .tickFormat(function(d) {
                        var dx = graphData[0].values[d] && graphData[0].values[d].x || 0;
                        return dx ? d3.time.format(timeFormat)(new Date(Number(dx+'000'))) : '';
                    });

                    job_status_chart.yAxis     //Chart y-axis settings
                    .axisLabel('JOBS')
                    .tickFormat(d3.format('.f'));

                    d3.select(element.find('svg')[0])
                    .datum(graphData)
                    .call(job_status_chart)
                    .style({
                        "font-family": 'Open Sans',
                        "font-style": "normal",
                        "font-weight":400,
                        "src": "url(/static/assets/OpenSans-Regular.ttf)"
                    });

                    // when the Period drop down filter is used, create a new graph based on the
                    $('.n').on("click", function(){
                        period = this.getAttribute("id");
                        $('#period-dropdown').replaceWith("<a id=\"period-dropdown\" class=\"DashboardGraphs-filterDropdownText\" role=\"button\" data-toggle=\"dropdown\" data-target=\"#\" href=\"/page.html\">"+this.text+
                        "<i class=\"fa fa-chevron-down DashboardGraphs-filterIcon\"></i>\n");
                        scope.$parent.isFailed = true;
                        scope.$parent.isSuccessful = true;
                        recreateGraph(period, job_type);
                    });

                    //On click, update with new data
                    $('.m').on("click", function(){
                        job_type = this.getAttribute("id");
                        $('#type-dropdown').replaceWith("<a id=\"type-dropdown\" class=\"DashboardGraphs-filterDropdownText\" role=\"button\" data-toggle=\"dropdown\" data-target=\"#\" href=\"/page.html\">"+this.text+
                        "<i class=\"fa fa-chevron-down DashboardGraphs-filterIcon\"></i>\n");
                        scope.$parent.isFailed = true;
                        scope.$parent.isSuccessful = true;
                        recreateGraph(period, job_type);
                    });
                    adjustGraphSize(job_status_chart, element);
                }

                function onResize() {
                    adjustGraphSize(job_status_chart, element);

                }

                angular.element($window).on('resize', onResize);
                $(".DashboardGraphs-graph--jobStatusGraph").resize(onResize);

                element.on('$destroy', function() {
                    angular.element($window).off('resize', onResize);
                    $(".DashboardGraphs-graph--jobStatusGraph").removeResize(onResize);
                });

                if (scope.removeGraphDataReady) {
                    scope.removeGraphDataReady();
                }

            }
        }
