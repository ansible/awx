import React, { useEffect, useCallback } from 'react';
import { string, number, shape, arrayOf } from 'prop-types';
import * as d3 from 'd3';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';
import { PageContextConsumer } from '@patternfly/react-core';

import ChartTooltip from './ChartTooltip';

function LineChart({ id, data, height, i18n, pageContext }) {
  const { isNavOpen } = pageContext;

  // Methods
  const draw = useCallback(() => {
    const margin = { top: 15, right: 15, bottom: 35, left: 70 };

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
      path
        .transition()
        .duration(1000)
        .attrTween('stroke-dasharray', tweenDash);
    }

    function tweenDash(...params) {
      const l = params[2][params[1]].getTotalLength();
      const i = d3.interpolateString(`0,${l}`, `${l},${l}`);
      return val => i(val);
    }

    const x = d3.scaleTime().rangeRound([0, width]);
    const y = d3.scaleLinear().range([height, 0]);

    // [success, fail, total]
    const colors = d3.scaleOrdinal(['#6EC664', '#A30000', '#06C']);
    const svg = d3
      .select(`#${id}`)
      .append('svg')
      .attr('width', width + margin.left + margin.right)
      .attr('height', height + margin.top + margin.bottom)
      // .attr('id', 'foo')
      .attr('z', 100)
      .append('g')
      .attr('id', 'chart-container')
      .attr('transform', `translate(${margin.left}, ${margin.top})`);
    // Tooltip
    const tooltip = new ChartTooltip({
      svg: `#${id}`,
      colors,
      label: i18n._(t`Jobs`),
      i18n,
    });
    const parseTime = d3.timeParse('%Y-%m-%d');

    const formattedData = data.reduce(
      (formatted, { created, successful, failed }) => {
        const DATE = parseTime(created) || new Date();
        const RAN = +successful || 0;
        const FAIL = +failed || 0;
        const TOTAL = +successful + failed || 0;
        return formatted.concat({ DATE, RAN, FAIL, TOTAL });
      },
      []
    );
    // Scale the range of the data
    const largestY = formattedData.reduce((a_max, b) => {
      const b_max = Math.max(b.RAN > b.FAIL ? b.RAN : b.FAIL);
      return a_max > b_max ? a_max : b_max;
    }, 0);
    x.domain(d3.extent(formattedData, d => d.DATE));
    y.domain([
      0,
      largestY > 4 ? largestY + Math.max(largestY / 10, 1) : 5,
    ]).nice();

    const successLine = d3
      .line()
      .curve(d3.curveMonotoneX)
      .x(d => x(d.DATE))
      .y(d => y(d.RAN));

    const failLine = d3
      .line()
      .defined(d => typeof d.FAIL === 'number')
      .curve(d3.curveMonotoneX)
      .x(d => x(d.DATE))
      .y(d => y(d.FAIL));
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
    svg.selectAll('.y-axis .tick text').attr('x', -5);

    // text label for the y axis
    svg
      .append('text')
      .attr('transform', 'rotate(-90)')
      .attr('y', 0 - margin.left)
      .attr('x', 0 - height / 2)
      .attr('dy', '1em')
      .style('text-anchor', 'middle')
      .text('Job Runs');

    // Add the X Axis
    let ticks;
    const maxTicks = Math.round(
      formattedData.length / (formattedData.length / 2)
    );
    ticks = formattedData.map(d => d.DATE);
    if (formattedData.length === 31) {
      ticks = formattedData
        .map((d, i) => (i % maxTicks === 0 ? d.DATE : undefined))
        .filter(item => item);
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
          .tickFormat(d3.timeFormat('%-m/%-d')) // "1/19"
      ) // "Jan-01"
      .selectAll('line')
      .attr('stroke', '#d7d7d7');

    svg.selectAll('.x-axis .tick text').attr('y', 10);

    // text label for the x axis
    svg
      .append('text')
      .attr(
        'transform',
        `translate(${width / 2} , ${height + margin.top + 20})`
      )
      .style('text-anchor', 'middle')
      .text('Date');
    const vertical = svg
      .append('path')
      .attr('class', 'mouse-line')
      .style('stroke', 'black')
      .style('stroke-width', '3px')
      .style('stroke-dasharray', '3, 3')
      .style('opacity', '0');

    const handleMouseOver = d => {
      tooltip.handleMouseOver(d);
      // show vertical line
      vertical.transition().style('opacity', '1');
    };

    const handleMouseMove = function mouseMove(...params) {
      const intersectX = params[2][params[1]].cx.baseVal.value;
      vertical.attr('d', () => `M${intersectX},${height} ${intersectX},${0}`);
    };

    const handleMouseOut = () => {
      // hide tooltip
      tooltip.handleMouseOut();
      // hide vertical line
      vertical.transition().style('opacity', 0);
    };

    // Add the successLine path.
    svg
      .append('path')
      .data([formattedData])
      .attr('class', 'line')
      .style('fill', 'none')
      .style('stroke', () => colors(1))
      .attr('stroke-width', 2)
      .attr('d', successLine)
      .call(transition);

    // Add the failLine path.
    svg
      .append('path')
      .data([formattedData])
      .attr('class', 'line')
      .style('fill', 'none')
      .style('stroke', () => colors(0))
      .attr('stroke-width', 2)
      .attr('d', failLine)
      .call(transition);

    const dateFormat = d3.timeFormat('%-m-%-d');

    // create our successLine circles
    svg
      .selectAll('dot')
      .data(formattedData)
      .enter()
      .append('circle')
      .attr('r', 3)
      .style('stroke', () => colors(1))
      .style('fill', () => colors(1))
      .attr('cx', d => x(d.DATE))
      .attr('cy', d => y(d.RAN))
      .attr('id', d => `success-dot-${dateFormat(d.DATE)}`)
      .on('mouseover', handleMouseOver)
      .on('mousemove', handleMouseMove)
      .on('mouseout', handleMouseOut);
    // create our failLine circles
    svg
      .selectAll('dot')
      .data(formattedData)
      .enter()
      .append('circle')
      .attr('r', 3)
      .style('stroke', () => colors(0))
      .style('fill', () => colors(0))
      .attr('cx', d => x(d.DATE))
      .attr('cy', d => y(d.FAIL))
      .attr('id', d => `success-dot-${dateFormat(d.DATE)}`)
      .on('mouseover', handleMouseOver)
      .on('mousemove', handleMouseMove)
      .on('mouseout', handleMouseOut);
  }, [data, height, i18n, id]);

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

LineChart.propTypes = {
  id: string.isRequired,
  data: arrayOf(shape({})).isRequired,
  height: number.isRequired,
};

const withPageContext = Component => {
  return function contextComponent(props) {
    return (
      <PageContextConsumer>
        {pageContext => <Component {...props} pageContext={pageContext} />}
      </PageContextConsumer>
    );
  };
};

export default withI18n()(withPageContext(LineChart));
