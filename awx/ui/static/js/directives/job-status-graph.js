angular.module('GraphDirectives', [])
  .directive('jobStatusGraph', ['$rootScope', '$compile', '$location' , '$window', 'Wait', 'jobStatusGraphData',
        function ($rootScope, $compile , $location, $window, Rest, Wait, jobStatusGraphData) {
            return {
              restrict: 'A',
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
                scope.$on('DataReceived:JobStatusGraph',
                          function(e, data) {
                            scope.$emit('graphDataReady', data);
                          })
            ]);

            function createGraph(period, jobtype){
              console.log('createGraph');
              // jobStatusGraphData.get(period, jobtype).then(function(data) {
              //   scope.$emit('graphDataReady', data);
              // });
            }

            cleanup = _.compose(
              [ cleanup,
                angular.element($window).bind('resize', function() {
                  if($(window).width()<500){
                    $('.graph-container').height(300);
                  }
                  else{
                    var winHeight = $(window).height(),
                    available_height = winHeight - $('#main-menu-container .navbar').outerHeight() - $('#count-container').outerHeight() - 120;
                    $('.graph-container').height(available_height/2);
                    job_status_chart.update();
                  }
                })
            ]);

            if (scope.removeGraphDataReady) {
              scope.removeGraphDataReady();
            }
            scope.removeGraphDataReady = scope.$on('graphDataReady', function (e, data) {

              console.log("building graph", data);

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

              var job_status_chart = nv.models.lineChart()
              .margin({top: 5, right: 75, bottom: 80, left: 85})  //Adjust chart margins to give the x-axis some breathing room.
              .x(function(d,i) { return i; })
              .useInteractiveGuideline(true)  //We want nice looking tooltips and a guideline!
              .transitionDuration(350)  //how fast do you want the lines to transition?
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
              .datum(graphData).transition()
              .attr('width', width)
              .attr('height', height)
              .duration(1000)
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
              d3.selectAll(element.find(".n")[0])
              .on("click", function() {
                period = this.getAttribute("id");
                $('#period-dropdown').replaceWith("<a id=\"period-dropdown\" role=\"button\" data-toggle=\"dropdown\" data-target=\"#\" href=\"/page.html\">"+this.text+"<span class=\"caret\"><span>\n");

                createGraph(period, job_type);
              });

              //On click, update with new data
              d3.selectAll(element.find(".m")[0])
              .on("click", function() {
                job_type = this.getAttribute("id");
                $('#type-dropdown').replaceWith("<a id=\"type-dropdown\" role=\"button\" data-toggle=\"dropdown\" data-target=\"#\" href=\"/page.html\">"+this.text+"<span class=\"caret\"><span>\n");

                createGraph(period, job_type);
              });

              return job_status_chart;

            });
          }
        }]);
