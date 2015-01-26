angular.module('DashboardGraphs')
  .directive('hostStatusGraph', ['$compile', '$window',
    function ($compile, $window) {
      return {
        restrict: 'E',
        link: link,
        templateUrl: '/static/partials/host_status_graph.html'
      };

      function link(scope, element, attr) {
        var html, canvas, context, winHeight, available_height, host_pie_chart;

        scope.$watch(attr.data, function(data) {
          if (data && data.hosts) {
            buildGraph(data);
          }
        });

        function adjustGraphSize() {
          var parentHeight = element.parent().parent().height();
          var toolbarHeight = element.find('.toolbar').height();
          var container = element.find('svg').parent();
          var margins = host_pie_chart.margin();

          var newHeight = parentHeight - toolbarHeight - margins.bottom;

          $(container).height(newHeight);

          host_pie_chart.update();
        }

        $window.addEventListener('resize', adjustGraphSize);

        element.on('$destroy', function() {
          $window.removeEventListener('resize', adjustGraphSize);
        });

        function buildGraph(data) {
          if(data.hosts.total+data.hosts.failed>0){
            data = [
              {
              "label": "Successful",
              "color": "#00aa00",
              "value" : data.hosts.total
            } ,
            {
              "label": "Failed",
              "color" : "#aa0000",
              "value" : data.hosts.failed
            }
            ];

            var width = $('.graph-container').width(), // nv.utils.windowSize().width/3,
            height = $('.graph-container').height()*0.7; //nv.utils.windowSize().height/5,
            host_pie_chart = nv.models.pieChart()
            .margin({top: 5, right: 75, bottom: 25, left: 85})
            .x(function(d) { return d.label; })
            .y(function(d) { return d.value; })
            .showLabels(true)
            .labelThreshold(0.01)
            .tooltipContent(function(x, y) {
              return '<b>'+x+'</b>'+ '<p>' +  Math.floor(y.replace(',','')) + ' Hosts ' +  '</p>';
            })
            .color(['#00aa00', '#aa0000']);

            host_pie_chart.pie.pieLabelsOutside(true).labelType("percent");

            d3.select(element.find('svg')[0])
            .datum(data)
            // .attr('width', width)
            // .attr('height', height)
            .transition().duration(350)
            .call(host_pie_chart)
            .style({
              "font-family": 'Open Sans',
              "font-style": "normal",
              "font-weight":400,
              "src": "url(/static/fonts/OpenSans-Regular.ttf)"
            });
            // nv.utils.windowResize(host_pie_chart.update);
            adjustGraphSize();
            return host_pie_chart;
          }
          else{
            winHeight = $($window).height();
            available_height = winHeight - $('#main-menu-container .navbar').outerHeight() - $('#count-container').outerHeight() - 120;
            element.find('.graph-wrapper').height(available_height/2);
            element.find('svg').replaceWith('<canvas id="circlecanvas" width="120" height="120"></canvas>');

            canvas = document.getElementById("circlecanvas");
            context = canvas.getContext("2d");
            context.arc(55, 55, 50, 0, Math.PI * 2, false);
            context.lineWidth = 1;
            context.strokeStyle = '#1778c3';
            context.stroke();
            context.font = "12px Open Sans";
            context.fillText("No Host data",18,55);
          }

        }
      }
  }]);
