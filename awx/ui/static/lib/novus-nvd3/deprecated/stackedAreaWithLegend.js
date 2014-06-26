
nv.models.stackedAreaWithLegend = function() {
  var margin = {top: 30, right: 20, bottom: 50, left: 60},
      getWidth = function() { return 960 },
      getHeight = function() { return 500 },
      color = d3.scale.category20().range(),
      showControls = true,
      showLegend = true;

  var x = d3.scale.linear(),
      y = d3.scale.linear(),
      getX = function(d) { return d.x },
      getY = function(d) { return d.y },
      xAxis = nv.models.axis().scale(x).orient('bottom'),
      yAxis = nv.models.axis().scale(y).orient('left'),
      legend = nv.models.legend().height(30),
      controls = nv.models.legend().height(30),
      stacked = nv.models.stackedArea(),
      dispatch = d3.dispatch('tooltipShow', 'tooltipHide');

  //TODO: let user select default
  var controlsData = [
    { key: 'Stacked' },
    { key: 'Stream', disabled: true },
    { key: 'Expanded', disabled: true }
  ];


  function chart(selection) {
    selection.each(function(data) {
      var width = getWidth(),
          height = getHeight(),
          availableWidth = width - margin.left - margin.right,
          availableHeight = height - margin.top - margin.bottom;

      var seriesData = data.filter(function(d) { return !d.disabled })
            .reduce(function(prev, curr, index) {  //sum up all the y's
                curr.values.forEach(function(d,i) {
                  if (!index) prev[i] = {x: getX(d,i), y:0};
                  prev[i].y += getY(d,i);
                });
                return prev;
              }, []);


      x   .domain(d3.extent(d3.merge(seriesData), function(d) { return d.x } ))
          .range([0, availableWidth]);

      y   .domain(stacked.offset() == 'zero' ?
            [0, d3.max(seriesData, function(d) { return d.y } )] :
            [0, 1]  // 0 - 100%
          )
          .range([availableHeight, 0]);

      stacked
        .width(availableWidth)
        .height(availableHeight)
        //.color(color)
        .color(data.map(function(d,i) {
          return d.color || color[i % 20];
        }).filter(function(d,i) { return !data[i].disabled }))


      var wrap = d3.select(this).selectAll('g.wrap.stackedAreaWithLegend').data([data]);
      var gEnter = wrap.enter().append('g').attr('class', 'wrap nvd3 stackedAreaWithLegend').append('g');

      gEnter.append('g').attr('class', 'x axis');
      gEnter.append('g').attr('class', 'y axis');
      gEnter.append('g').attr('class', 'stackedWrap');
      gEnter.append('g').attr('class', 'legendWrap');
      gEnter.append('g').attr('class', 'controlsWrap');


      var g = wrap.select('g');


      if (showLegend) {
        //TODO: margins should be adjusted based on what components are used: axes, axis labels, legend
        margin.top = legend.height();

        legend
          .width(width/2 - margin.right)
          .color(color);

        g.select('.legendWrap')
            .datum(data)
            .attr('transform', 'translate(' + (width/2 - margin.left) + ',' + (-margin.top) +')')
            .call(legend);
      }


      if (showControls) {
        controls.width(280).color(['#444', '#444', '#444']);
        g.select('.controlsWrap')
            .datum(controlsData)
            .attr('transform', 'translate(0,' + (-margin.top) +')')
            .call(controls);
      }


      g.attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');


      var stackedWrap = g.select('.stackedWrap')
          .datum(data);
      d3.transition(stackedWrap).call(stacked);


      xAxis
        .domain(x.domain())
        .range(x.range())
        .ticks( width / 100 )
        .tickSize(-availableHeight, 0);

      g.select('.x.axis')
          .attr('transform', 'translate(0,' + availableHeight + ')');
      d3.transition(g.select('.x.axis'))
          .call(xAxis);

      yAxis
        .domain(y.domain())
        .range(y.range())
        .ticks(stacked.offset() == 'wiggle' ? 0 : height / 36)
        .tickSize(-availableWidth, 0)
        .tickFormat(stacked.offset() == 'zero' ? d3.format(',.2f') : d3.format('%')); //TODO: stacked format should be set by caller

      d3.transition(g.select('.y.axis'))
          .call(yAxis);



      //TODO: FIX Logic error, screws up when series are disabled by clicking legend, then series are desiabled by clicking the area
      stacked.dispatch.on('areaClick.toggle', function(e) {
        if (data.filter(function(d) { return !d.disabled }).length === 1)
          data = data.map(function(d) { 
            if (d.disabled)
              d.values.map(function(p) { p.y = p._y || p.y; return p }); // ....

            d.disabled = false; 

            return d 
          });
        else
          data = data.map(function(d,i) { 
            if (!d.disabled && i !== e.seriesIndex)
              d.values.map(function(p) { p._y = p.y; p.y = 0; return p }); //TODO: need to use value from getY, not always d.y

            if (d.disabled && i === e.seriesIndex)
              d.values.map(function(p) { p.y = p._y || p.y; return p }); // ....

            d.disabled = (i != e.seriesIndex); 

            return d 
          });

        selection.transition().call(chart);
      });
      legend.dispatch.on('legendClick', function(d,i) { 
        d.disabled = !d.disabled;

        if (d.disabled)
          d.values.map(function(p) { p._y = p.y; p.y = 0; return p }); //TODO: need to use value from getY, not always d.y
        else
          d.values.map(function(p) { p.y = p._y; return p }); // ....

        if (!data.filter(function(d) { return !d.disabled }).length) {
          data.map(function(d) {
            d.disabled = false;
            d.values.map(function(p) { p.y = p._y; return p }); // ....
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
          case 'Stacked':
            stacked.style('stack');
            break;
          case 'Stream':
            stacked.style('stream');
            break;
          case 'Expanded':
            stacked.style('expand');
            break;
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

      stacked.dispatch.on('tooltipShow', function(e) {
        //disable tooltips when value ~= 0
        //// TODO: consider removing points from voronoi that have 0 value instead of this hack
        if (!Math.round(getY(e.point) * 100)) {  // 100 will not be good for very small numbers... will have to think about making this valu dynamic, based on data range
          setTimeout(function() { d3.selectAll('.point.hover').classed('hover', false) }, 0);
          return false;
        }

        e.pos = [e.pos[0] + margin.left, e.pos[1] + margin.top],
        dispatch.tooltipShow(e);
      });

      stacked.dispatch.on('tooltipHide', function(e) {
        dispatch.tooltipHide(e);
      });
    });



    /*
    // If the legend changed the margin's height, need to recalc positions... should think of a better way to prevent duplicate work
    if (margin.top != legend.height())
      chart(selection);
     */


    return chart;
  }


  chart.dispatch = dispatch;
  chart.stacked = stacked;
  chart.xAxis = xAxis;
  chart.yAxis = yAxis;

  d3.rebind(chart, stacked, 'interactive', 'offset', 'order', 'style', 'clipEdge', 'size', 'forceX', 'forceY', 'forceSize');

  chart.x = function(_) {
    if (!arguments.length) return getX;
    getX = d3.functor(_); //not used locally, so could jsut be a rebind
    stacked.x(getX);
    return chart;
  };

  chart.y = function(_) {
    if (!arguments.length) return getY;
    getY = d3.functor(_);
    stacked.y(getY);
    return chart;
  };

  chart.margin = function(_) {
    if (!arguments.length) return margin;
    margin = _;
    return chart;
  };

  chart.width = function(_) {
    if (!arguments.length) return getWidth;
    getWidth = d3.functor(_);
    return chart;
  };

  chart.height = function(_) {
    if (!arguments.length) return getHeight;
    getHeight = d3.functor(_);
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
