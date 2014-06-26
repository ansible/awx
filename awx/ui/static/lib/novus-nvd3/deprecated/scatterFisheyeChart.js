
nv.models.scatterFisheyeChart = function() {
  var margin = {top: 30, right: 20, bottom: 50, left: 60},
      width = null,
      height = null,
      color = nv.utils.defaultColor(),
      showDistX = false,
      showDistY = false,
      showLegend = true,
      showControls = true,
      fisheye = 0,
      tooltips = true,
      tooltipX = function(key, x, y) { return '<strong>' + x + '</strong>' },
      tooltipY = function(key, x, y) { return '<strong>' + y + '</strong>' },
      tooltip = function(key, x, y, e, graph) { 
        return '<h3>' + key + '</h3>' +
               '<p>' +  y + ' at ' + x + '</p>'
      },
      noData = "No Data Available."
      ;

  var x = d3.fisheye.scale(d3.scale.linear).distortion(0),
      y = d3.fisheye.scale(d3.scale.linear).distortion(0);

  var scatter = nv.models.scatter().xScale(x).yScale(y),
      //x = scatter.xScale(),
      //y = scatter.yScale(),
      xAxis = nv.models.axis().orient('bottom').scale(x).tickPadding(10),
      yAxis = nv.models.axis().orient('left').scale(y).tickPadding(10),
      legend = nv.models.legend().height(30),
      controls = nv.models.legend().height(30),
      dispatch = d3.dispatch('tooltipShow', 'tooltipHide'),
      x0, y0; //TODO: abstract distribution component and have old scales stored there

  var showTooltip = function(e, offsetElement) {
    //TODO: make tooltip style an option between single or dual on axes (maybe on all charts with axes?)

    //var left = e.pos[0] + ( offsetElement.offsetLeft || 0 ),
        //top = e.pos[1] + ( offsetElement.offsetTop || 0),
    var leftX = e.pos[0] + ( offsetElement.offsetLeft || 0 ),
        topX = y.range()[0] + margin.top + ( offsetElement.offsetTop || 0),
        leftY = x.range()[0] + margin.left + ( offsetElement.offsetLeft || 0 ),
        topY = e.pos[1] + ( offsetElement.offsetTop || 0),
        xVal = xAxis.tickFormat()(scatter.x()(e.point, e.pointIndex)),
        yVal = yAxis.tickFormat()(scatter.y()(e.point, e.pointIndex)),
        contentX = tooltipX(e.series.key, xVal, yVal, e, chart),
        contentY = tooltipY(e.series.key, xVal, yVal, e, chart);
        //content = tooltip(e.series.key, xVal, yVal, e, chart);

    nv.tooltip.show([leftX, topX], contentX, 'n', 1, offsetElement);
    nv.tooltip.show([leftY, topY], contentY, 'e', 1, offsetElement);
    //nv.tooltip.show([left, top], content, e.value < 0 ? 'n' : 's');
  };

  var controlsData = [
    { key: 'Magnify', disabled: true }
  ];

  function chart(selection) {
    selection.each(function(data) {
      var container = d3.select(this),
          that = this;

      //TODO: decide if this makes sense to add into all the models for ease of updating (updating without needing the selection)
      chart.update = function() { selection.transition().call(chart) };


      var availableWidth = (width  || parseInt(container.style('width')) || 960)
                             - margin.left - margin.right,
          availableHeight = (height || parseInt(container.style('height')) || 400)
                             - margin.top - margin.bottom;


      //------------------------------------------------------------
      // Display No Data message if there's nothing to show.

      if (!data || !data.length || !data.filter(function(d) { return d.values.length }).length) {
        container.append('text')
          .attr('class', 'nvd3 nv-noData')
          .attr('x', availableWidth / 2)
          .attr('y', availableHeight / 2)
          .attr('dy', '-.7em')
          .style('text-anchor', 'middle')
          .text(noData);
          return chart;
      } else {
        container.select('.nv-noData').remove();
      }

      //------------------------------------------------------------



      x0 = x0 || scatter.xScale();
      y0 = y0 || scatter.yScale();


      var wrap = container.selectAll('g.nv-wrap.nv-scatterChart').data([data]);
      var gEnter = wrap.enter().append('g').attr('class', 'nvd3 nv-wrap nv-scatterChart nv-chart-' + scatter.id()).append('g');


      gEnter.append('rect')
          .attr('class', 'nvd3 nv-background')
          .attr('width', availableWidth)
          .attr('height', availableHeight);


      gEnter.append('g').attr('class', 'nv-legendWrap');
      gEnter.append('g').attr('class', 'nv-x nv-axis');
      gEnter.append('g').attr('class', 'nv-y nv-axis');
      gEnter.append('g').attr('class', 'nv-scatterWrap');
      gEnter.append('g').attr('class', 'nv-controlsWrap');
      //gEnter.append('g').attr('class', 'nv-distWrap');

      var g = wrap.select('g')

      if (showLegend) {
        legend.width( availableWidth / 2 );

        wrap.select('.nv-legendWrap')
            .datum(data)
            .call(legend);

        if ( margin.top != legend.height()) {
          margin.top = legend.height();
          availableHeight = (height || parseInt(container.style('height')) || 400)
                             - margin.top - margin.bottom;
        }

        wrap.select('.nv-legendWrap')
            .attr('transform', 'translate(' + (availableWidth / 2) + ',' + (-margin.top) +')');
      }


      scatter
        .width(availableWidth)
        .height(availableHeight)
        .color(data.map(function(d,i) {
          return d.color || color(d, i);
        }).filter(function(d,i) { return !data[i].disabled }))


      if (showControls) {
        controls.width(180).color(['#444']);
        g.select('.nv-controlsWrap')
            .datum(controlsData)
            .attr('transform', 'translate(0,' + (-margin.top) +')')
            .call(controls);
      }


      g.attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');


      var scatterWrap = wrap.select('.nv-scatterWrap')
          .datum(data.filter(function(d) { return !d.disabled }));
      d3.transition(scatterWrap).call(scatter);


      xAxis
        .ticks( availableWidth / 100 )
        .tickSize( -availableHeight , 0);

      g.select('.nv-x.nv-axis')
          .attr('transform', 'translate(0,' + y.range()[0] + ')');
      d3.transition(g.select('.nv-x.nv-axis'))
          .call(xAxis);


      yAxis
        .ticks( availableHeight / 36 )
        .tickSize( -availableWidth, 0);

      d3.transition(g.select('.nv-y.nv-axis'))
          .call(yAxis);




      //TODO abstract Distribution into its own component
      if ( showDistX || showDistY) {
        var distWrap = scatterWrap.selectAll('g.nv-distribution')
            .data(function(d) { return d }, function(d) { return d.key });

        distWrap.enter().append('g').attr('class', function(d,i) { return 'nv-distribution nv-series-' + i })

        distWrap.style('stroke', function(d,i) { return color.filter(function(d,i) { return data[i] && !data[i].disabled })[i % color.length] })
      }

      if (showDistX) {
        var distX = distWrap.selectAll('line.nv-distX')
              .data(function(d) { return d.values })
        distX.enter().append('line')
            .attr('x1', function(d,i) { return x0(scatter.x()(d,i)) })
            .attr('x2', function(d,i) { return x0(scatter.x()(d,i)) })
        //d3.transition(distX.exit())
        d3.transition(distWrap.exit().selectAll('line.nv-distX'))
            .attr('x1', function(d,i) { return x(scatter.x()(d,i)) })
            .attr('x2', function(d,i) { return x(scatter.x()(d,i)) })
            .remove();
        distX
            .attr('class', function(d,i) { return 'nv-distX nv-distX-' + i })
            .attr('y1', y.range()[0])
            .attr('y2', y.range()[0] + 8);
        d3.transition(distX)
            .attr('x1', function(d,i) { return x(scatter.x()(d,i)) })
            .attr('x2', function(d,i) { return x(scatter.x()(d,i)) })
      }


      if (showDistY) {
        var distY = distWrap.selectAll('line.nv-distY')
            .data(function(d) { return d.values })
        distY.enter().append('line')
            .attr('y1', function(d,i) { return y0(scatter.y()(d,i)) })
            .attr('y2', function(d,i) { return y0(scatter.y()(d,i)) });
        //d3.transition(distY.exit())
        d3.transition(distWrap.exit().selectAll('line.nv-distY'))
            .attr('y1', function(d,i) { return y(scatter.y()(d,i)) })
            .attr('y2', function(d,i) { return y(scatter.y()(d,i)) })
            .remove();
        distY
            .attr('class', function(d,i) { return 'nv-distY nv-distY-' + i })
            .attr('x1', x.range()[0])
            .attr('x2', x.range()[0] - 8)
        d3.transition(distY)
            .attr('y1', function(d,i) { return y(scatter.y()(d,i)) })
            .attr('y2', function(d,i) { return y(scatter.y()(d,i)) });
      }




      legend.dispatch.on('legendClick', function(d,i, that) {
        d.disabled = !d.disabled;

        if (!data.filter(function(d) { return !d.disabled }).length) {
          data.map(function(d) {
            d.disabled = false;
            wrap.selectAll('.nv-series').classed('disabled', false);
            return d;
          });
        }

        selection.transition().call(chart)
      });

      controls.dispatch.on('legendClick', function(d,i) { 
        d.disabled = !d.disabled;

        fisheye = d.disabled ? 0 : 2.5;
        g.select('.nv-background').style('pointer-events', d.disabled ? 'none' : 'all');
        scatter.interactive(d.disabled);
        tooltips = d.disabled;

        if (d.disabled) {
          x.distortion(fisheye).focus(0);
          y.distortion(fisheye).focus(0);

          scatterWrap.call(scatter);
          g.select('.nv-x.nv-axis').call(xAxis);
          g.select('.nv-y.nv-axis').call(yAxis);
        }

        selection.transition().call(chart);
      });

      /*
      legend.dispatch.on('legendMouseover', function(d, i) {
        d.hover = true;
        selection.transition().call(chart)
      });

      legend.dispatch.on('legendMouseout', function(d, i) {
        d.hover = false;
        selection.transition().call(chart)
      });
      */


      scatter.dispatch.on('elementMouseover.tooltip', function(e) {
        //scatterWrap.select('.series-' + e.seriesIndex + ' .distX-' + e.pointIndex)
        d3.select('.nv-chart-' + scatter.id() + ' .nv-series-' + e.seriesIndex + ' .nv-distX-' + e.pointIndex)
            .attr('y1', e.pos[1]);
        //scatterWrap.select('.series-' + e.seriesIndex + ' .distY-' + e.pointIndex)
        d3.select('.nv-chart-' + scatter.id() + ' .nv-series-' + e.seriesIndex + ' .nv-distY-' + e.pointIndex)
            .attr('x1', e.pos[0]);

        e.pos = [e.pos[0] + margin.left, e.pos[1] + margin.top];
        dispatch.tooltipShow(e);
      });
      //if (tooltips) dispatch.on('tooltipShow', function(e) { showTooltip(e, container[0][0].parentNode) } ); // TODO: maybe merge with above?
      dispatch.on('tooltipShow', function(e) {
        if (tooltips) showTooltip(e, that.parentNode);
      });

      scatter.dispatch.on('elementMouseout.tooltip', function(e) {
        dispatch.tooltipHide(e);

        //scatterWrap.select('.series-' + e.seriesIndex + ' .distX-' + e.pointIndex)
        d3.select('.nv-chart-' + scatter.id() + ' .nv-series-' + e.seriesIndex + ' .nv-distX-' + e.pointIndex)
            .attr('y1', y.range()[0]);
        //scatterWrap.select('.series-' + e.seriesIndex + ' .distY-' + e.pointIndex)
        d3.select('.nv-chart-' + scatter.id() + ' .nv-series-' + e.seriesIndex + ' .nv-distY-' + e.pointIndex)
            .attr('x1', x.range()[0]);
      });
      dispatch.on('tooltipHide', nv.tooltip.cleanup);



      //TODO: get distributions to work with fisheye
      g.select('.nv-background').on('mousemove', updateFisheye);
      g.select('.nv-point-paths').on('mousemove', updateFisheye);

      function updateFisheye() {
        var mouse = d3.mouse(this);
        x.distortion(fisheye).focus(mouse[0]);
        y.distortion(fisheye).focus(mouse[1]);

        scatterWrap.call(scatter);
        g.select('.nv-x.nv-axis').call(xAxis);
        g.select('.nv-y.nv-axis').call(yAxis);
      }

      //store old scales for use in transitions on update, to animate from old to new positions, and sizes
      x0 = x.copy();
      y0 = y.copy();

    });

    return chart;
  }


  chart.dispatch = dispatch;
  chart.legend = legend;
  chart.xAxis = xAxis;
  chart.yAxis = yAxis;

  d3.rebind(chart, scatter, 'interactive', 'shape', 'size', 'xScale', 'yScale', 'zScale', 'xDomain', 'yDomain', 'sizeDomain', 'forceX', 'forceY', 'forceSize', 'clipVoronoi', 'clipRadius', 'fisheye', 'fisheyeRadius');


  chart.margin = function(_) {
    if (!arguments.length) return margin;
    margin = _;
    return chart;
  };

  chart.width = function(_) {
    if (!arguments.length) return width;
    width = _;
    return chart;
  };

  chart.height = function(_) {
    if (!arguments.length) return height;
    height = _;
    return chart;
  };

  chart.color = function(_) {
    if (!arguments.length) return color;
    color = nv.utils.getColor(_);
    legend.color(color);
    return chart;
  };

  chart.showDistX = function(_) {
    if (!arguments.length) return showDistX;
    showDistX = _;
    return chart;
  };

  chart.showDistY = function(_) {
    if (!arguments.length) return showDistY;
    showDistY = _;
    return chart;
  };

  chart.showControls = function(_) {
    if (!arguments.length) return showControls;
    showControls = _;
    return chart;
  };

  chart.showLegend = function(_) {
    if (!arguments.length) return showLegend;
    showLegend = _;
    return chart;
  };

  chart.fisheye = function(_) {
    if (!arguments.length) return fisheye;
    fisheye = _;
    return chart;
  };

  chart.tooltips = function(_) {
    if (!arguments.length) return tooltips;
    tooltips = _;
    return chart;
  };

  chart.tooltipContent = function(_) {
    if (!arguments.length) return tooltip;
    tooltip = _;
    return chart;
  };

  chart.noData = function(_) {
    if (!arguments.length) return noData;
    noData = _;
    return chart;
  };


  return chart;
}
