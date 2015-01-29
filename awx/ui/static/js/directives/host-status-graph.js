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
            createGraph(data);
          }
        });

        function adjustGraphSize() {

          if (angular.isUndefined(host_pie_chart)) {
            return;
          }

          var parentHeight = element.parent().parent().height();
          var toolbarHeight = element.find('.toolbar').height();
          var container = element.find('svg').parent();
          var margins = host_pie_chart.margin();

          var newHeight = parentHeight - toolbarHeight - margins.bottom;

          $(container).height(newHeight);

          host_pie_chart.update();
        }

        angular.element($window).on('resize', adjustGraphSize);

        element.on('$destroy', function() {
          angular.element($window).off('resize', adjustGraphSize);
        });

        function createGraph(data) {
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
            .transition().duration(350)
            .call(host_pie_chart)
            .style({
              "font-family": 'Open Sans',
              "font-style": "normal",
              "font-weight":400,
              "src": "url(/static/fonts/OpenSans-Regular.ttf)"
            });

            adjustGraphSize();
            return host_pie_chart;
          }
          else{
            // This should go in a template or something
            // but I'm at the end of a card and need to get this done.
            // We definitely need to refactor this, I'm letting
            // good enough be good enough for right now.
            var notFoundContainer = $('<div></div>');
            notFoundContainer.css({
              'text-align': 'center',
              'width': '100%',
              'padding-top': '2em'
            });

            notFoundContainer.text('No host data');

            element.find('svg').replaceWith(notFoundContainer);
          }

        }
      }
  }]);
