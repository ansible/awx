
nv.models.cumulativeLine = function() {
  var margin = {top: 30, right: 20, bottom: 30, left: 60},
      getWidth = function() { return 960 },
      getHeight = function() { return 500 },
      color = d3.scale.category20().range(),
      dotRadius = function() { return 2.5 },
      getX = function(d) { return d.x },
      getY = function(d) { return d.y },
      id = Math.floor(Math.random() * 10000), //Create semi-unique ID incase user doesn't select one
      showRescaleToggle = true,
      rescaleY = true;

  var x = d3.scale.linear(),
      dx = d3.scale.linear(),
      y = d3.scale.linear(),
      xAxis = nv.models.axis().scale(x).orient('bottom'),
      yAxis = nv.models.axis().scale(y).orient('left'),
      legend = nv.models.legend().height(30),
      controls = nv.models.legend().height(30),
      lines = nv.models.line(),
      dispatch = d3.dispatch('tooltipShow', 'tooltipHide'),
      index = {i: 0, x: 0};

  //TODO: let user select default
  var controlsData = [
    { key: 'Re-scale y-axis' }
  ];

  var indexDrag = d3.behavior.drag()
                    .on('dragstart', dragStart)
                    .on('drag', dragMove)
                    .on('dragend', dragEnd);

  function dragStart(d,i) {}

  function dragMove(d,i) {
    d.x += d3.event.dx;
    d.i = Math.round(dx.invert(d.x));

    //d3.transition(d3.select('.chart-' + id)).call(chart);
    d3.select(this).attr("transform", "translate(" + dx(d.i) + ",0)");
  }

  function dragEnd(d,i) {
    d3.transition(d3.select('.chart-' + id)).call(chart);
  }


  function chart(selection) {
    selection.each(function(data) {
      var width = getWidth(),
          height = getHeight(),
          availableWidth = width - margin.left - margin.right,
          availableHeight = height - margin.top - margin.bottom;

      var series = indexify(index.i, data);

      var seriesData = series
            .filter(function(d) { return !rescaleY || !d.disabled }) // only filter out if rescaling y axis
            .map(function(d) { return d.values });


      x   .domain(d3.extent(d3.merge(seriesData), function(d) { return d.x } ))
          .range([0, availableWidth]);

      dx  .domain([0, data[0].values.length - 1]) //Assumes all series have same length
          .range([0, availableWidth])
          .clamp(true);

      y   .domain(d3.extent(d3.merge(seriesData), function(d) { return d.y } ))
          .range([availableHeight, 0]);


      lines
        .width(availableWidth)
        .height(availableHeight)
        .color(data.map(function(d,i) {
          return d.color || color[i % color.length];
        }).filter(function(d,i) { return !data[i].disabled }))


      var wrap = d3.select(this).classed('chart-' + id, true).selectAll('g.wrap').data([series]);
      var gEnter = wrap.enter().append('g').attr('class', 'wrap nvd3 cumulativeLine').append('g');

      gEnter.append('g').attr('class', 'x axis');
      gEnter.append('g').attr('class', 'y axis');
      gEnter.append('g').attr('class', 'linesWrap');
      gEnter.append('g').attr('class', 'legendWrap');
      gEnter.append('g').attr('class', 'controlsWrap');



      //TODO: margins should be adjusted based on what components are used: axes, axis labels, legend
      margin.top = legend.height();

      var g = wrap.select('g')
          .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');


      legend.width(width/2 - margin.right);

      g.select('.legendWrap')
          .datum(data)
          .attr('transform', 'translate(' + (width/2 - margin.left) + ',' + (-margin.top) +')')
          .call(legend);

      if (showRescaleToggle) {
        controls.width(140).color(['#444', '#444', '#444']);
        g.select('.controlsWrap')
            .datum(controlsData)
            .attr('transform', 'translate(0,' + (-margin.top) +')')
            .call(controls);
      }


      var linesWrap = g.select('.linesWrap')
          .datum(series.filter(function(d) { return !d.disabled }))


      d3.transition(linesWrap).call(lines);


      var indexLine = linesWrap.selectAll('.indexLine')
          .data([index]);
      indexLine.enter().append('rect').attr('class', 'indexLine')
          .attr('width', 3)
          .attr('x', -2)
          .attr('fill', 'red')
          .attr('fill-opacity', .5)
          .call(indexDrag)

      indexLine
          .attr("transform", function(d) { return "translate(" + dx(d.i) + ",0)" })
          .attr('height', availableHeight)


      xAxis
        .domain(x.domain())
        .range(x.range())
        .ticks( width / 100 )
        .tickSize(-availableHeight, 0);

      g.select('.x.axis')
          .attr('transform', 'translate(0,' + y.range()[0] + ')');
      d3.transition(g.select('.x.axis'))
          .call(xAxis);

      yAxis
        .domain(y.domain())
        .range(y.range())
        .ticks( height / 36 )
        .tickSize(-availableWidth, 0);

      d3.transition(g.select('.y.axis'))
          .call(yAxis);





      // ********** EVENT LISTENERS **********

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


      controls.dispatch.on('legendClick', function(d,i) { 
        d.disabled = !d.disabled;
        rescaleY = !d.disabled;

        //console.log(d,i,arguments);

        selection.transition().call(chart);
      });




      lines.dispatch.on('elementMouseover.tooltip', function(e) {
        dispatch.tooltipShow({
          point: e.point,
          series: e.series,
          pos: [e.pos[0] + margin.left, e.pos[1] + margin.top],
          seriesIndex: e.seriesIndex,
          pointIndex: e.pointIndex
        });
      });

      lines.dispatch.on('elementMouseout.tooltip', function(e) {
        dispatch.tooltipHide(e);
      });


    });

    return chart;
  }



  // ********** FUNCTIONS **********

  /* Normalize the data according to an index point. */
  function indexify(idx, data) {
    return data.map(function(line, i) {
      var v = getY(line.values[idx], idx);

      return {
        key: line.key,
        values: line.values.map(function(point, pointIndex) {
          return {'x': getX(point, pointIndex), 'y': (getY(point, pointIndex) - v) / (1 + v) };
        }),
        disabled: line.disabled,
        hover: line.hover
        /*
        if (v < -.9) {
          //if a series loses more than 100%, calculations fail.. anything close can cause major distortion (but is mathematically currect till it hits 100)
        }
        */
      };
    });
  };




  // ********** PUBLIC ACCESSORS **********

  chart.dispatch = dispatch;

  chart.x = function(_) {
    if (!arguments.length) return getX;
    getX = _;
    //lines.x(_);
    return chart;
  };

  chart.y = function(_) {
    if (!arguments.length) return getY;
    getY = _;
    //lines.y(_);
    return chart;
  };

  chart.margin = function(_) {
    if (!arguments.length) return margin;
    margin = _;
    return chart;
  };

  /*
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
  */

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

  chart.color = function(_) {
    if (!arguments.length) return color;
    color = _;
    legend.color(_);
    return chart;
  };

  chart.dotRadius = function(_) {
    if (!arguments.length) return dotRadius;
    dotRadius = d3.functor(_);
    lines.dotRadius = _;
    return chart;
  };

  chart.showRescaleToggle = function(_) {
    if (!arguments.length) return showRescaleToggle;
    showRescaleToggle = _;
    return chart;
  };


  // Expose the x-axis' tickFormat method.
  //chart.xAxis = {};
  //d3.rebind(chart.xAxis, xAxis, 'tickFormat');
  chart.xAxis = xAxis;

  // Expose the y-axis' tickFormat method.
  //chart.yAxis = {};
  //d3.rebind(chart.yAxis, yAxis, 'tickFormat');
  chart.yAxis = yAxis;


  return chart;
}
