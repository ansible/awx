import React, { useEffect, useCallback } from 'react';
import { string, number, shape, arrayOf } from 'prop-types';
import * as d3 from 'd3';
import { t } from '@lingui/macro';
import { PageContextConsumer } from '@patternfly/react-core';
import UsageChartTooltip from './UsageChartTooltip';

function UsageChart({ id, data, height, pageContext }) {
  const { isNavOpen } = pageContext;

  // Methods
  const draw = useCallback(() => {
    const margin = { top: 15, right: 25, bottom: 105, left: 70 };

    const getWidth = () => {
      let width;
      // This is in an a try/catch due to an error from jest.
      // Even though the d3.select returns a valid selector with
      // style function, it says it is null in the test
      try {
        width =
          parseInt(d3.select(`#${id}`).style('width'), 10) -
            margin.left -
            margin.right || 700;
      } catch (error) {
        width = 700;
      }
      return width;
    };

    // Clear our chart container element first
    d3.selectAll(`#${id} > *`).remove();
    const width = getWidth();

    function transition(path) {
      path.transition().duration(1000).attrTween('stroke-dasharray', tweenDash);
    }

    function tweenDash(...params) {
      const l = params[2][params[1]].getTotalLength();
      const i = d3.interpolateString(`0,${l}`, `${l},${l}`);
      return (val) => i(val);
    }

    const x = d3.scaleTime().rangeRound([0, width]);
    const y = d3.scaleLinear().range([height, 0]);

    // [consumed, capacity]
    const colors = d3.scaleOrdinal(['#06C', '#C9190B']);
    const svg = d3
      .select(`#${id}`)
      .append('svg')
      .attr('width', width + margin.left + margin.right)
      .attr('height', height + margin.top + margin.bottom)
      .attr('z', 100)
      .append('g')
      .attr('id', 'chart-container')
      .attr('transform', `translate(${margin.left}, ${margin.top})`);
    // Tooltip
    const tooltip = new UsageChartTooltip({
      svg: `#${id}`,
      colors,
      label: t`Hosts`,
    });

    const parseTime = d3.timeParse('%Y-%m-%d');

    const formattedData = data?.reduce(
      (formatted, { date, license_consumed, license_capacity }) => {
        const MONTH = parseTime(date);
        const CONSUMED = +license_consumed;
        const CAPACITY = +license_capacity;
        return formatted.concat({ MONTH, CONSUMED, CAPACITY });
      },
      []
    );

    // Scale the range of the data
    const largestY = formattedData?.reduce((a_max, b) => {
      const b_max = Math.max(b.CONSUMED > b.CAPACITY ? b.CONSUMED : b.CAPACITY);
      return a_max > b_max ? a_max : b_max;
    }, 0);
    x.domain(d3.extent(formattedData, (d) => d.MONTH));
    y.domain([
      0,
      largestY > 4 ? largestY + Math.max(largestY / 10, 1) : 5,
    ]).nice();

    const capacityLine = d3
      .line()
      .curve(d3.curveMonotoneX)
      .x((d) => x(d.MONTH))
      .y((d) => y(d.CAPACITY));

    const consumedLine = d3
      .line()
      .curve(d3.curveMonotoneX)
      .x((d) => x(d.MONTH))
      .y((d) => y(d.CONSUMED));

    // Add the Y Axis
    svg
      .append('g')
      .attr('class', 'y-axis')
      .call(
        d3
          .axisLeft(y)
          .ticks(
            largestY > 3
              ? Math.min(largestY + Math.max(largestY / 10, 1), 10)
              : 5
          )
          .tickSize(-width)
          .tickFormat(d3.format('d'))
      )
      .selectAll('line')
      .attr('stroke', '#d7d7d7');
    svg.selectAll('.y-axis .tick text').attr('x', -5).attr('font-size', '14');

    // text label for the y axis
    svg
      .append('text')
      .attr('transform', 'rotate(-90)')
      .attr('y', 0 - margin.left)
      .attr('x', 0 - height / 2)
      .attr('dy', '1em')
      .style('text-anchor', 'middle')
      .text(t`Unique Hosts`);

    // Add the X Axis
    let ticks;
    const maxTicks = Math.round(
      formattedData.length / (formattedData.length / 2)
    );
    ticks = formattedData.map((d) => d.MONTH);
    if (formattedData.length === 13) {
      ticks = formattedData
        .map((d, i) => (i % maxTicks === 0 ? d.MONTH : undefined))
        .filter((item) => item);
    }

    svg.select('.domain').attr('stroke', '#d7d7d7');

    svg
      .append('g')
      .attr('class', 'x-axis')
      .attr('transform', `translate(0, ${height})`)
      .call(
        d3
          .axisBottom(x)
          .tickValues(ticks)
          .tickSize(-height)
          .tickFormat(d3.timeFormat('%m/%y'))
      )
      .selectAll('line')
      .attr('stroke', '#d7d7d7');

    svg
      .selectAll('.x-axis .tick text')
      .attr('x', -25)
      .attr('font-size', '14')
      .attr('transform', 'rotate(-65)');

    // text label for the x axis
    svg
      .append('text')
      .attr(
        'transform',
        `translate(${width / 2} , ${height + margin.top + 50})`
      )
      .style('text-anchor', 'middle')
      .text(t`Month`);
    const vertical = svg
      .append('path')
      .attr('class', 'mouse-line')
      .style('stroke', 'black')
      .style('stroke-width', '3px')
      .style('stroke-dasharray', '3, 3')
      .style('opacity', '0');

    const handleMouseOver = (event, d) => {
      tooltip.handleMouseOver(event, d);
      // show vertical line
      vertical.transition().style('opacity', '1');
    };
    const handleMouseMove = function mouseMove(event) {
      const [pointerX] = d3.pointer(event);
      vertical.attr('d', () => `M${pointerX},${height} ${pointerX},${0}`);
    };

    const handleMouseOut = () => {
      // hide tooltip
      tooltip.handleMouseOut();
      // hide vertical line
      vertical.transition().style('opacity', 0);
    };

    const dateFormat = d3.timeFormat('%m/%y');

    // Add the consumed line path
    svg
      .append('path')
      .data([formattedData])
      .attr('class', 'line')
      .style('fill', 'none')
      .style('stroke', () => colors(1))
      .attr('stroke-width', 2)
      .attr('d', consumedLine)
      .call(transition);

    // create our consumed line circles

    svg
      .selectAll('dot')
      .data(formattedData)
      .enter()
      .append('circle')
      .attr('r', 3)
      .style('stroke', () => colors(1))
      .style('fill', () => colors(1))
      .attr('cx', (d) => x(d.MONTH))
      .attr('cy', (d) => y(d.CONSUMED))
      .attr('id', (d) => `consumed-dot-${dateFormat(d.MONTH)}`)
      .on('mouseover', (event, d) => handleMouseOver(event, d))
      .on('mousemove', handleMouseMove)
      .on('mouseout', handleMouseOut);

    // Add the capacity line path
    svg
      .append('path')
      .data([formattedData])
      .attr('class', 'line')
      .style('fill', 'none')
      .style('stroke', () => colors(0))
      .attr('stroke-width', 2)
      .attr('d', capacityLine)
      .call(transition);

    // create our capacity line circles

    svg
      .selectAll('dot')
      .data(formattedData)
      .enter()
      .append('circle')
      .attr('r', 3)
      .style('stroke', () => colors(0))
      .style('fill', () => colors(0))
      .attr('cx', (d) => x(d.MONTH))
      .attr('cy', (d) => y(d.CAPACITY))
      .attr('id', (d) => `capacity-dot-${dateFormat(d.MONTH)}`)
      .on('mouseover', handleMouseOver)
      .on('mousemove', handleMouseMove)
      .on('mouseout', handleMouseOut);

    // Create legend
    const legend_keys = [t`Subscriptions consumed`, t`Subscription capacity`];
    let totalWidth = width / 2 - 175;

    const lineLegend = svg
      .selectAll('.lineLegend')
      .data(legend_keys)
      .enter()
      .append('g')
      .attr('class', 'lineLegend')
      .each(function formatLegend() {
        const current = d3.select(this);
        current.attr('transform', `translate(${totalWidth}, ${height + 90})`);
        totalWidth += 200;
      });

    lineLegend
      .append('text')
      .text((d) => d)
      .attr('font-size', '14')
      .attr('transform', 'translate(15,9)'); // align texts with boxes

    lineLegend
      .append('rect')
      .attr('fill', (d) => colors(d))
      .attr('width', 10)
      .attr('height', 10);
  }, [data, height, id]);

  useEffect(() => {
    draw();
  }, [draw, isNavOpen]);

  useEffect(() => {
    function handleResize() {
      draw();
    }

    window.addEventListener('resize', handleResize);

    handleResize();

    return () => window.removeEventListener('resize', handleResize);
  }, [draw]);

  return <div id={id} />;
}

UsageChart.propTypes = {
  id: string.isRequired,
  data: arrayOf(shape({})).isRequired,
  height: number.isRequired,
};

const withPageContext = (Component) =>
  function contextComponent(props) {
    return (
      <PageContextConsumer>
        {(pageContext) => <Component {...props} pageContext={pageContext} />}
      </PageContextConsumer>
    );
  };

export default withPageContext(UsageChart);
