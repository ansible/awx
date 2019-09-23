/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default
    [   '$window',
        'adjustGraphSize',
        'templateUrl',
        'i18n',
        'moment',
        'jobStatusGraphData',
        JobStatusGraph
    ];

function JobStatusGraph($window, adjustGraphSize, templateUrl, i18n, moment, graphDataService) {
            return {
                restrict: 'E',
                scope: {
                    data: '=',
                    period: '=',
                    jobType: '=',
                    status: '='
                },
                templateUrl: templateUrl('home/dashboard/graphs/job-status/job_status_graph'),
                link: link
            };

            function link(scope, element) {
                var job_status_chart = nv.models.lineChart();

                scope.$watchCollection('data', function(value) {
                    if (value) {
                        createGraph(scope.period, scope.jobType, value, scope.status);
                    }
                });

                function recreateGraph(period, jobType, status) {
                    graphDataService.get(period, jobType, status)
                        .then(function(data) {
                            scope.data = data;
                            scope.period = period;
                            scope.jobType = jobType;
                            scope.status = Object.is(status, undefined) ? scope.status : status;
                        });
                }

                function createGraph(period, jobtype, data, status){
                    scope.period = period;
                    scope.jobType = jobtype;
                    scope.status = status;

                    var timeFormat, graphData = [
                        {   "color": "#5CB85C",
                            "key": i18n._("SUCCESSFUL"),
                            "values": data.jobs.successful
                        },
                        {   "key" : i18n._("FAILED") ,
                            "color" : "#D9534F",
                            "values": data.jobs.failed
                        }
                    ];

                    graphData = _.reject(graphData, function(num){
                        if(status!== undefined && status === num.key.toLowerCase()){
                            return num;
                        }
                    });

                    if(period === "day") {
                        timeFormat="H:mm";
                    }
                    else {
                        timeFormat = "MMM D";
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
                    .useInteractiveGuideline(true)  //We want nice looking tooltips and a guideline!
                    .showLegend(false)       //Show the legend, allowing users to turn on/off line series.
                    .showYAxis(true)        //Show the y-axis
                    .showXAxis(true)        //Show the x-axis
                    .margin({ right: 32 });

                    job_status_chart.interactiveLayer.tooltip.fixedTop(-10); //distance from the top of the chart to tooltip
                    job_status_chart.interactiveLayer.tooltip.distance(-1); //distance from interactive line to tooltip

                    scope.$on('$destroy', function() {
                        job_status_chart.tooltip.hidden(true);
                        job_status_chart.interactiveLayer.tooltip.hidden(true);
                    });

                    job_status_chart.xAxis
                    .axisLabel(i18n._("TIME"))//.showMaxMin(true)
                    .tickFormat(function(d) {
                        if (d) {
                            const tickDate = new Date(Number(d + '000'));
                            return moment(tickDate).format(timeFormat);
                        }
                        else {
                            return '';
                        }
                    });

                    job_status_chart.yAxis     //Chart y-axis settings
                    .axisLabel(i18n._('JOBS'))
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
                    $('.n').off('click').on("click", function(){
                        $('#period-dropdown-display')
                            .html(`
                                <span>${this.text}</span>
                                <i class="fa fa-angle-down DashboardGraphs-filterIcon"></i>
                            `);

                        scope.$parent.isFailed = true;
                        scope.$parent.isSuccessful = true;
                        recreateGraph(this.getAttribute("id"), scope.jobType, scope.status);
                    });

                    //On click, update with new data
                    $('.m').off('click').on("click", function(){
                        $('#type-dropdown-display')
                            .html(`
                                <span>${this.text}</span>
                                <i class="fa fa-angle-down DashboardGraphs-filterIcon"></i>
                            `);

                        scope.$parent.isFailed = true;
                        scope.$parent.isSuccessful = true;
                        recreateGraph(scope.period, this.getAttribute("id"), scope.status);
                    });

                    $('.o').off('click').on('click', function() {
                        $('#status-dropdown-display')
                            .html(`
                                <span>${this.text}</span>
                                <i class="fa fa-angle-down DashboardGraphs-filterIcon"></i>
                            `);

                        recreateGraph(scope.period, scope.jobType, this.getAttribute("id"));
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
