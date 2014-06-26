
nv.models.multiBarWithLegend = function() {
  var margin = {top: 30, right: 20, bottom: 50, left: 60},
      width = function() { return 960 },
      height = function() { return 500 },
      color = d3.scale.category20().range(),
      showControls = true,
      showLegend = true;

  //var x = d3.scale.linear(),
  var x = d3.scale.ordinal(),
      y = d3.scale.linear(),
      xAxis = nv.models.axis().scale(x).orient('bottom').highlightZero(false),
      yAxis = nv.models.axis().scale(y).orient('left'),
      legend = nv.models.legend().height(30),
      controls = nv.models.legend().height(30),
      multibar = nv.models.multiBar().stacked(false),
      dispatch = d3.dispatch('tooltipShow', 'tooltipHide');

  //TODO: let user select default
  var controlsData = [
    { key: 'Grouped' },
    { key: 'Stacked', disabled: true }
  ];

  function chart(selection) {
    selection.each(function(data) {
      var availableWidth = width() - margin.left - margin.right,
          availableHeight = height() - margin.top - margin.bottom,
          seriesData;

      if (multibar.stacked()) {
        seriesData = data.filter(function(d) { return !d.disabled })
          .reduce(function(prev, curr, index) {  //sum up all the y's
              curr.values.forEach(function(d,i) {
                if (!index) prev[i] = {x: multibar.x()(d,i), y:0};
                prev[i].y += multibar.y()(d,i);
              });
              return prev;
            }, []);
      } else {
        seriesData = data.filter(function(d) { return !d.disabled })
          .map(function(d) { 
            return d.values.map(function(d,i) {
              return { x: multibar.x()(d,i), y: multibar.y()(d,i) }
            })
          });
      }


      //x   .domain(d3.extent(d3.merge(seriesData).map(function(d) { return d.x }).concat(multibar.forceX) ))
          //.range([0, availableWidth]);

      x   .domain(d3.merge(seriesData).map(function(d) { return d.x }))
          .rangeBands([0, availableWidth], .1);
          //.rangeRoundBands([0, availableWidth], .1);

      y   .domain(d3.extent(d3.merge(seriesData).map(function(d) { return d.y }).concat(multibar.forceY) ))
          .range([availableHeight, 0]);

      multibar
        .width(availableWidth)
        .height(availableHeight)
        //.xDomain(x.domain())
        //.yDomain(y.domain())
        .color(data.map(function(d,i) {
          return d.color || color[i % 20];
        }).filter(function(d,i) { return !data[i].disabled }))



      var wrap = d3.select(this).selectAll('g.wrap.multiBarWithLegend').data([data]);
      var gEnter = wrap.enter().append('g').attr('class', 'wrap nvd3 multiBarWithLegend').append('g');

      gEnter.append('g').attr('class', 'x axis');
      gEnter.append('g').attr('class', 'y axis');
      gEnter.append('g').attr('class', 'linesWrap');
      gEnter.append('g').attr('class', 'legendWrap');
      gEnter.append('g').attr('class', 'controlsWrap');



      var g = wrap.select('g');


      if (showLegend) {
        //TODO: margins should be adjusted based on what components are used: axes, axis labels, legend
        margin.top = legend.height();

        legend.width(availableWidth / 2);

        g.select('.legendWrap')
            .datum(data)
            .attr('transform', 'translate(' + (availableWidth / 2) + ',' + (-margin.top) +')')
            .call(legend);
      }

      if (showControls) {
        controls.width(180).color(['#444', '#444', '#444']);
        g.select('.controlsWrap')
            .datum(controlsData)
            .attr('transform', 'translate(0,' + (-margin.top) +')')
            .call(controls);
      }


      g.attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

      var linesWrap = g.select('.linesWrap')
          .datum(data.filter(function(d) { return !d.disabled }))


      d3.transition(linesWrap).call(multibar);


      xAxis
        .scale(x)
        //.domain(x.domain())
        //.range(x.range())
        .ticks( availableWidth / 100 )
        .tickSize(-availableHeight, 0);

      g.select('.x.axis')
          .attr('transform', 'translate(0,' + y.range()[0] + ')');
      d3.transition(g.select('.x.axis'))
          .call(xAxis);

      var xTicks = g.select('.x.axis').selectAll('g');

      xTicks
          .selectAll('line, text')
          .style('opacity', 1)

      xTicks.filter(function(d,i) {
            return i % Math.ceil(data[0].values.length / (availableWidth / 100)) !== 0;
          })
          .selectAll('line, text')
          .style('opacity', 0)

      yAxis
        .domain(y.domain())
        .range(y.range())
        .ticks( availableHeight / 36 )
        .tickSize( -availableWidth, 0);

      d3.transition(g.select('.y.axis'))
          .call(yAxis);




      legend.dispatch.on('legendClick', function(d,i) {
        d.disabled = !d.disabled;

        if (!data.filter(function(d) { return !d.disabled }).length) {
          data.map(function(d) {
            d.disabled = false;
            wrap.selectAll('.series').classed('disabled', false);
            return d;
          });
        }

        selection.transition().call(chart);
      });

      controls.dispatch.on('legendClick', function(d,i) { 
        if (!d.disabled) return;
        controlsData = controlsData.map(function(s) {
          s.disabled = true;
          return s;
        });
        d.disabled = false;

        switch (d.key) {
          case 'Grouped':
            multibar.stacked(false);
            break;
          case 'Stacked':
            multibar.stacked(true);
            break;
        }

        selection.transition().call(chart);
      });


      multibar.dispatch.on('elementMouseover.tooltip', function(e) {
        e.pos = [e.pos[0] +  margin.left, e.pos[1] + margin.top];
        dispatch.tooltipShow(e);
      });

      multibar.dispatch.on('elementMouseout.tooltip', function(e) {
        dispatch.tooltipHide(e);
      });

    });

    return chart;
  }


  chart.dispatch = dispatch;
  chart.legend = legend;
  chart.xAxis = xAxis;
  chart.yAxis = yAxis;

  d3.rebind(chart, multibar, 'x', 'y', 'xDomain', 'yDomain', 'forceX', 'forceY', 'clipEdge', 'id', 'stacked');


  chart.margin = function(_) {
    if (!arguments.length) return margin;
    margin = _;
    return chart;
  };

  chart.width = function(_) {
    if (!arguments.length) return width;
    width = d3.functor(_);
    return chart;
  };

  chart.height = function(_) {
    if (!arguments.length) return height;
    height = d3.functor(_);
    return chart;
  };

  chart.color = function(_) {
    if (!arguments.length) return color;
    color = _;
    legend.color(_);
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


  return chart;
}
