angular.module('DashboardGraphs')
  .directive('jobStatusGraph', ['$rootScope', '$compile', '$location' , '$window', 'Wait', 'adjustGraphSize', 'jobStatusGraphData',
        function ($rootScope, $compile , $location, $window, Wait, adjustGraphSize, jobStatusGraphData) {
            return {
              restrict: 'E',
              templateUrl: '/static/partials/job_status_graph.html',
              link: link
            };

          function link(scope, element, attr) {
            var html, url, job_status_chart,
            period="month",
            job_type="all";

            var cleanup = angular.noop;

            var data;
            scope.$watch(attr.data, function(value) {
              if (value) {
                scope.$emit('graphDataReady', value);
              }
            });

            scope.$on('$destroy', cleanup);

            cleanup = _.compose(
              [ cleanup,
            ]);

            function createGraph(period, jobtype){
              jobStatusGraphData.get(period, jobtype).then(function(data) {
                scope.$emit('graphDataReady', data);
              });
            }

            var w = angular.element($window);


            $window.addEventListener('resize', function() {
              adjustGraphSize(job_status_chart, element);
            });

            if (scope.removeGraphDataReady) {
              scope.removeGraphDataReady();
            }

            var job_status_chart;
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

              job_status_chart = nv.models.lineChart()
              .margin({top: 5, right: 75, bottom: 50, left: 85})  //Adjust chart margins to give the x-axis some breathing room.
              .x(function(d,i) { return i; })
              .useInteractiveGuideline(true)  //We want nice looking tooltips and a guideline!
              .showLegend(true)       //Show the legend, allowing users to turn on/off line series.
              .showYAxis(true)        //Show the y-axis
              .showXAxis(true)        //Show the x-axis
              //  .width(width)
              // .height(height)
              ;


              var width = $('.graph-container').width(); // nv.utils.windowSize().width/3,
              var height = $('.graph-container').height()*0.7; //nv.utils.windowSize().height/5,

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
              // .attr('width', width)
              // .attr('height', height)
              // .transition().duration(100)
              .call(job_status_chart)
              .style({
                // 'width': width,
                // 'height': height,
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

                createGraph(period, job_type);
              });

              //On click, update with new data
              d3.selectAll(element.find(".m"))
              .on("click", function() {
                job_type = this.getAttribute("id");
                $('#type-dropdown').replaceWith("<a id=\"type-dropdown\" role=\"button\" data-toggle=\"dropdown\" data-target=\"#\" href=\"/page.html\">"+this.text+"<span class=\"caret\"><span>\n");

                createGraph(period, job_type);
              });

              adjustGraphSize(job_status_chart, element);

              return job_status_chart;

            });
          }
        }]);
