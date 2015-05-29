export default
    [   '$rootScope',
        '$compile',
        '$location' ,
        '$window',
        'Wait',
        'adjustGraphSize',
        'jobStatusGraphData',
        JobStatusGraph
    ];

function JobStatusGraph($rootScope, $compile , $location, $window, Wait, adjustGraphSize, graphDataService) {
            return {
                restrict: 'E',
                scope: {
                    data: '='
                },
                templateUrl: '/static/js/dashboard/graphs/job-status/job_status_graph.partial.html',
                link: link
            };

            function link(scope, element) {
                var job_type, job_status_chart = nv.models.lineChart();

                scope.period="month";
                scope.jobType="all";

                scope.$watch('data', function(value) {
                    if (value) {
                        createGraph(scope.period, scope.jobType, value);
                    }
                }, true);

                function recreateGraph(period, jobType) {
                    graphDataService.get(period, jobType)
                        .then(function(data) {
                            scope.data = data;
                            scope.period = period;
                            scope.jobType = jobType;
                        });

                }

                function createGraph(period, jobtype, data){
                    scope.period = period;
                    scope.jobType = jobtype;

                    var timeFormat, graphData = [
                        {   "color": "#60D66F",
                            "key": "Successful",
                            "values": data.jobs.successful
                        },
                        {   "key" : "Failed" ,
                            "color" : "#ff5850",
                            "values": data.jobs.failed
                        }
                    ];

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
                    .showLegend(true)       //Show the legend, allowing users to turn on/off line series.
                    .showYAxis(true)        //Show the y-axis
                    .showXAxis(true);       //Show the x-axis


                    job_status_chart.xAxis
                    .axisLabel("Time")//.showMaxMin(true)
                    .tickFormat(function(d) {
                        var dx = graphData[0].values[d] && graphData[0].values[d].x || 0;
                        return dx ? d3.time.format(timeFormat)(new Date(Number(dx+'000'))) : '';
                    });

                    job_status_chart.yAxis     //Chart y-axis settings
                    .axisLabel('Jobs')
                    .tickFormat(d3.format('.f'));

                    d3.select(element.find('svg')[0])
                    .datum(graphData)
                    .call(job_status_chart)
                    .style({
                        "font-family": 'Open Sans',
                        "font-style": "normal",
                        "font-weight":400,
                        "src": "url(/static/fonts/OpenSans-Regular.ttf)"
                    });

                    // when the Period drop down filter is used, create a new graph based on the
                    d3.selectAll(element.find(".n"))
                    .on("click", function() {
                        period = this.getAttribute("id");
                        $('#period-dropdown').replaceWith("<a id=\"period-dropdown\" role=\"button\" data-toggle=\"dropdown\" data-target=\"#\" href=\"/page.html\">"+this.text+"<span class=\"caret\"><span>\n");

                        recreateGraph(period, job_type);
                    });

                    //On click, update with new data
                    d3.selectAll(element.find(".m"))
                    .on("click", function() {
                        job_type = this.getAttribute("id");
                        $('#type-dropdown').replaceWith("<a id=\"type-dropdown\" role=\"button\" data-toggle=\"dropdown\" data-target=\"#\" href=\"/page.html\">"+this.text+"<span class=\"caret\"><span>\n");

                        recreateGraph(period, job_type);
                    });

                    job_status_chart.legend.margin({top: 1, right:0, left:24, bottom: 0});

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
