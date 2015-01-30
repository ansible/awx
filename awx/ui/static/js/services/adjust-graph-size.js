angular.module('DashboardGraphs').
    factory('adjustGraphSize', function() {


    // Adjusts the size of graphs based on the current height
    // of the outer parent (see auto-size-module directive).
    //
    // Since the graph's svg element is set to width & height of 100%,
    // it will automatically size itself when the size of its container
    // changes. Since boxes in HTML automatically fill the width of their
    // parent, we don't have to change the container's width. However,
    // since the makers HTML never heard of vertical rhythm,
    // we have to manually set a new height on the container.
    //
    // ## Calculating the container's new height
    //
    // newHeight is the height we assign to the graph's immediate parent.
    // This is calculated as the height of the graph-container (the
    // outer parent), offset by the height of the toolbar row
    // (the contains the title and/or any filters) and the
    // bottom margin.
    //
    // ## Responsive Graph Stuff
    //
    // Letting the svg element automatically scale only solves part of
    // the responsive graph problem. d3 draws graphs as paths, with static
    // positioning of all elements. Therefore, we need to tell the graph how
    // to adjust itself so that it can resize properly.
    //
    // ### Resizing the axes
    //
    // First we get the width & height of the chart after it has been modified
    // by setting the height on its parent (see Calculating the New Container's
    // Height above). Note that we need to offset the width/height by the margins
    // to make sure we keep all the spacing intact.
    //
    // Next, we update the range for x & y to take the new width & height into
    // account. d3 uses this range to map domain values (the actual data) onto
    // pixels.
    //
    // After that we adjust the number of ticks on the axes. This makes sure we
    // will never have overlapping ticks. If that does become a problem, try
    // changing the divisor in the calculations to a different number until you
    // find something that helps. For example, (width / 75) should make the x
    // axis only ever display 1 tick per every 75 pixels.
    //
    // ### Redrawing the line
    //
    // Since this is a line graph, now that we've changed the range & ticks,
    // we need to instruct d3 to repaint (redraw) the actual lines representing
    // the data. We do this by setting the "d" attribute of the path element
    // that represents the line to the line function on the chart model. This
    // function triggers the mapping of domain to range, and plots the chart.
    // Calling chartModel.update() at the end instructs nv to process our changes.
    //
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
        .attr('d', chartModel.lines);

        chartModel.update();
    };
});
