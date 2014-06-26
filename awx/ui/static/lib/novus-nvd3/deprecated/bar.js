
nv.models.bar = function() {
  var margin = {top: 20, right: 10, bottom: 80, left: 60},
      width = 960,
      height = 500,
      animate = 500,
      label ='label',
      rotatedLabel = true,
      showLabels = true,
      id = Math.floor(Math.random() * 10000), //Create semi-unique ID in case user doesn't select one
      color = d3.scale.category20(),
      field ='y',
      title = '';

  var x = d3.scale.ordinal(),
      y = d3.scale.linear(),
      xAxis = d3.svg.axis().scale(x).orient('bottom'),
      yAxis = d3.svg.axis().scale(y).orient('left'),
      dispatch = d3.dispatch('chartClick', 'elementClick', 'elementDblClick', 'tooltipShow', 'tooltipHide');


  function chart(selection) {
    selection.each(function(data) {
      x .domain(data.map(function(d,i) { return d[label]; }))
        .rangeRoundBands([0, width - margin.left - margin.right], .1);


      var min = d3.min(data, function(d) { return d[field] });
      var max = d3.max(data, function(d) { return d[field] });
      var x0 = Math.max(-min, max);
      var x1 = -x0;

      // If we have no negative values, then lets stack this with just positive bars
      if (min >= 0) x1 = 0;

      y .domain([x1, x0])
        .range([height - margin.top - margin.bottom, 0])
        .nice();

      xAxis.ticks( width / 100 );
      yAxis.ticks( height / 36 ).tickSize(-(width - margin.right - margin.left), 0);

      var parent = d3.select(this)
          .on("click", function(d,i) {
            dispatch.chartClick({
                data: d,
                index: i,
                pos: d3.event,
                id: id
            });
          });


      var wrap = parent.selectAll('g.wrap').data([data]);
      var gEnter = wrap.enter();
      gEnter.append("text")
          .attr("class", "title")
          .attr("dy", ".91em")
          .attr("text-anchor", "start")
          .text(title);
      gEnter = gEnter.append('g').attr('class', 'nvd3 wrap').attr('id','wrap-'+id).append('g');



      gEnter.append('g').attr('class', 'x axis');
      gEnter.append('g').attr('class', 'y axis');
      gEnter.append('g').attr('class', 'bars');


      wrap.attr('width', width)
          .attr('height', height);

      var g = wrap.select('g')
          .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');


      var bars = wrap.select('.bars').selectAll('.bar')
          .data(function(d) { return d; });

      bars.exit().remove();


      var barsEnter = bars.enter().append('svg:rect')
          .attr('class', function(d) { return d[field] < 0 ? "bar negative" : "bar positive"})
          .attr("fill", function(d, i) { return color(i); })
          .attr('x', 0 )
          .on('mouseover', function(d,i){
            d3.select(this).classed('hover', true);
            dispatch.tooltipShow({
                label: d[label],
                value: d[field],
                data: d,
                index: i,
                // TODO: Calculate the center to the bar
                pos: [d3.event.pageX, d3.event.pageY],
                id: id
            });

          })
          .on('mouseout', function(d,i){
                d3.select(this).classed('hover', false);
                dispatch.tooltipHide({
                    label: d[label],
                    value: d[field],
                    data: d,
                    index: i,
                    id: id
                });
          })
          .on('click', function(d,i) {
                dispatch.elementClick({
                    label: d[label],
                    value: d[field],
                    data: d,
                    index: i,
                    pos: d3.event,
                    id: id
                });
              d3.event.stopPropagation();
          })
          .on('dblclick', function(d,i) {
              dispatch.elementDblClick({
                  label: d[label],
                  value: d[field],
                  data: d,
                  index: i,
                  pos: d3.event,
                  id: id
              });
              d3.event.stopPropagation();
          });


      bars
          .attr('class', function(d) { return d[field] < 0 ? "bar negative" : "bar positive"})
          .attr('transform', function(d,i) { return 'translate(' + x(d[label]) + ',0)'; })
          .attr('width', x.rangeBand )
          .order()
          .transition()
          .duration(animate)
          .attr('y', function(d) {  return y(Math.max(0, d[field])); })
          .attr('height', function(d) { return Math.abs(y(d[field]) - y(0));  });


      g.select('.x.axis')
          .attr('transform', 'translate(0,' + y.range()[0] + ')')
          .call(xAxis);


      if (rotatedLabel) {
        g.select('.x.axis').selectAll('text').attr('text-anchor','start').attr("transform", function(d) {
          return "rotate(35)translate(" + this.getBBox().height/2 + "," + '0' + ")";
        });
      }
      if (!showLabels) {
        g.select('.x.axis').selectAll('text').attr('fill', 'rgba(0,0,0,0)');
        g.select('.x.axis').selectAll('line').attr('style', 'opacity: 0');
      }
      /*else {
        g.select('.x.axis').selectAll('text').attr('fill', 'rgba(0,0,0,1)');
        g.select('.x.axis').selectAll('line').attr('style', 'opacity: 1');
      }*/



      g.select('.y.axis')
        .call(yAxis);
    });

    return chart;
  }

  chart.margin = function(_) {
    if (!arguments.length) return margin;
    margin = _;
    return chart;
  };

  chart.width = function(_) {
    if (!arguments.length) return width;
    if (margin.left + margin.right + 20 > _)
      width = margin.left + margin.right + 20; // Min width
    else
      width = _;
    return chart;
  };

  chart.height = function(_) {
    if (!arguments.length) return height;
    if (margin.top + margin.bottom + 20 > _)
      height = margin.top + margin.bottom + 20; // Min height
    else
      height = _;
    return chart;
  };

  chart.animate = function(_) {
    if (!arguments.length) return animate;
    animate = _;
    return chart;
  };

  chart.labelField = function(_) {
    if (!arguments.length) return (label);
      label = _;
      return chart;
  };

  chart.dataField = function(_) {
    if (!arguments.length) return (field);
    field = _;
    return chart;
  };

  chart.id = function(_) {
        if (!arguments.length) return id;
        id = _;
        return chart;
  };

  chart.rotatedLabel = function(_) {
        if (!arguments.length) return rotatedLabel;
        rotatedLabel = _;
        return chart;
  };

  chart.showLabels = function(_) {
        if (!arguments.length) return (showLabels);
        showLabels = _;
        return chart;
  };

  chart.title = function(_) {
      if (!arguments.length) return (title);
      title = _;
      return chart;
  };

  chart.xaxis = {};
  // Expose the x-axis' tickFormat method.
  d3.rebind(chart.xaxis, xAxis, 'tickFormat');

  chart.yaxis = {};
  // Expose the y-axis' tickFormat method.
  d3.rebind(chart.yaxis, yAxis, 'tickFormat');

  chart.dispatch = dispatch;

  return chart;
}
