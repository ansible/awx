angular.module('DashboardGraphs').
  directive('hostCountGraph', ['GetBasePath', 'Rest', function(getBasePath, Rest) {

  return {
    restrict: 'E',
    templateUrl: '/static/partials/host_count_graph.html',
    link: link
  };

  function link(scope, element, attrs) {
    var url, license, license_graph;

    url = getBasePath('config');

    if (scope.removeResizeHostGraph) {
      scope.removeResizeHostGraph();
    }
    scope.removeResizeHostGraph= scope.$on('ResizeHostGraph', function () {
      if($(window).width()<500){
        $('.graph-container').height(300);
      }
      else{
        var winHeight = $(window).height(),
        available_height = winHeight - $('#main-menu-container .navbar').outerHeight() - $('#count-container').outerHeight() - 120;
        $('.graph-container').height(available_height/2);
        license_graph.update();
      }
    });

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
      url = getBasePath('dashboard')+'graphs/inventory/';
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

      //url = getBasePath('dashboard')+'graphs/';
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
          height = $('.graph-container').height()*0.6; //nv.utils.windowSize().height/5,
          license_graph = nv.models.lineChart()
          .margin({top: 15, right: 75, bottom: 40, left: 85})
          .x(function(d,i) { return i ;})
          .useInteractiveGuideline(true)  //We want nice looking tooltips and a guideline!
          .transitionDuration(350)  //how fast do you want the lines to transition?
          .showLegend(true)       //Show the legend, allowing users to turn on/off line series.
          .showYAxis(true)        //Show the y-axis
          .showXAxis(true)        //Show the x-axis
          ;

          license_graph.xAxis
          .axisLabel("Time")
          .tickFormat(function(d) {
            var dx = graphData[0].values[d] && graphData[0].values[d].x || 0;
            return dx ? d3.time.format('%m/%d')(new Date(Number(dx+'000'))) : '';
          });

          license_graph.yAxis     //Chart y-axis settings
          .axisLabel('Hosts')
          .tickFormat(d3.format('.f'));

          d3.select(element.find('svg')[0])
          .datum(graphData).transition()
          .attr('width', width)
          .attr('height', height)
          .duration(500)
          .call(license_graph)
          .style({
            // 'width': width,
            // 'height': height,
            "font-family": 'Open Sans',
            "font-style": "normal",
            "font-weight":400,
            "src": "url(/static/fonts/OpenSans-Regular.ttf)"
          });


          // nv.utils.windowResize(license_graph.update);
          scope.$emit('WidgetLoaded');
          return license_graph;

        }
      });
    });
  }
}]);
