angular.module('DashboardGraphs').
  factory('adjustGraphSize', function() {
      return function adjustGraphSize(chartModel, element) {
        var parentHeight = element.parent().parent().height();
        var toolbarHeight = element.find('.toolbar').height();
        var container = element.find('svg').parent();
        var margins = chartModel.margin();

        var newHeight = parentHeight - toolbarHeight - margins.bottom;

        $(container).height(newHeight);

        var graph = d3.select(element.find('svg')[0]);
        var width = parseInt(graph.style('width')) - margins.left - margins.right;
        var height = parseInt(graph.style('height')) - margins.top - margins.bottom;

        chartModel.xRange([0, width]);
        chartModel.yRange([height, 0]);

        chartModel.xAxis.ticks(Math.max(width / 75, 2));
        chartModel.yAxis.ticks(Math.max(height / 50, 2));

        if (height < 160) {
          graph.select('.y.nv-axis').select('.domain').style('display', 'none');
          graph.select('.y.nv-axis').select('.domain').style('display', 'initial');
        }

        graph.select('.x.nv-axis')
          .attr('transform', 'translate(0, ' + height + ')')
          .call(chartModel.xAxis);

        graph.selectAll('.line')
              .attr('d', chartModel.lines)

        chartModel.update();
      }
});
