import React, { useEffect, useCallback } from 'react';
import { t } from '@lingui/macro';
import * as d3 from 'd3';

function LineChart({ data, helpText }) {
  const count = data[0]?.values.length;
  const draw = useCallback(() => {
    const margin = 80;
    const getWidth = () => {
      let width;
      // This is in an a try/catch due to an error from jest.
      // Even though the d3.select returns a valid selector with
      // style function, it says it is null in the test
      try {
        width =
          parseInt(d3.select(`#chart`).style('width'), 10) - margin || 700;
      } catch (error) {
        width = 700;
      }

      return width;
    };
    const width = getWidth();
    const height = 500;
    const duration = 250;
    const circleRadius = 6;
    const circleRadiusHover = 8;

    /* Scale */
    let smallestY;
    let largestY;
    data.map((line) =>
      line.values.forEach((value) => {
        if (smallestY === undefined) {
          smallestY = value.y;
        }
        if (value.y < smallestY) {
          smallestY = value.y;
        }
        if (largestY === undefined) {
          largestY = smallestY + 10;
        }
        if (value.y > largestY) {
          largestY = value.y;
        }
      })
    );

    const xScale = d3
      .scaleLinear()
      .domain(
        d3.max(data[0].values, (d) => d.x) > 49
          ? d3.extent(data[0].values, (d) => d.x)
          : [0, 50]
      )
      .range([0, width - margin]);

    const yScale = d3
      .scaleLinear()
      .domain([smallestY, largestY])
      .range([height - margin, 0]);

    const color = d3.scaleOrdinal(d3.schemeCategory10);

    /* Add SVG */
    d3.selectAll(`#chart > *`).remove();

    const renderTooltip = (d) => {
      d3.selectAll(`.tooltip > *`).remove();

      d3.select('#chart')
        .append('span')
        .attr('class', 'tooltip')
        .attr('stroke', 'black')
        .attr('fill', 'white')
        .style('padding-left', '50px');
      const tooltip = {};
      data.map((datum) => {
        datum.values.forEach((value) => {
          if (d.x === value.x) {
            tooltip[datum.name] = value.y;
          }
        });
        return tooltip;
      });
      Object.entries(tooltip).forEach(([key, value], i) => {
        d3.select('.tooltip')
          .append('span')
          .attr('class', 'tooltip-text-wrapper')
          .append('text')
          .attr('class', 'tooltip-text')
          .style('color', color(i))
          .style('padding-right', '20px')
          .text(`${key}: ${value}`);
      });
    };
    const removeTooltip = () => {
      d3.select('.tooltip')
        .style('cursor', 'none')
        .selectAll(`.tooltip > *`)
        .remove();
    };

    // Add legend
    d3.selectAll(`.legend > *`).remove();
    const legendContainer = d3
      .select('#chart')
      .append('div')
      .style('display', 'flex')
      .attr('class', 'legend')
      .attr('height', '400px')
      .attr('width', '500px')
      .style('padding-left', '50px');

    legendContainer
      .append('text')
      .attr('class', 'legend-title')
      .attr('x', '100')
      .attr('y', '50')
      .text(t`Legend`);

    legendContainer.data(data, (d, i) => {
      if (d?.name) {
        const legendItemContainer = legendContainer
          .append('div')
          .style('display', 'flex')
          .attr('id', 'legend-item-container')
          .style('padding-left', '20px');

        legendItemContainer
          .append('div')
          .style('background-color', color(i))
          .style('height', '8px')
          .style('width', '8px')
          .style('border-radius', '50%')
          .style('padding', '5px')
          .style('margin-top', '6px');

        legendItemContainer
          .append('text')
          .style('padding-left', '20px')
          .text(d.name);
      }
    });

    // Add help text to top of chart

    d3.select('#chart')
      .append('div')
      .attr('class', 'help-text')
      .style('padding-left', '50px')
      .style('padding-top', '20px')
      .text(helpText);

    const svg = d3
      .select('#chart')
      .append('svg')
      .attr('width', `${width + margin}px`)
      .attr('height', `${height + margin}px`)
      .append('g')
      .attr('transform', `translate(${margin}, ${margin})`);

    /* Add line into SVG */
    const line = d3
      .line()
      .curve(d3.curveMonotoneX)
      .x((d) => xScale(d.x))
      .y((d) => yScale(d.y));

    const lines = svg.append('g');

    lines
      .selectAll('.line-group')
      .data(data)
      .enter()
      .append('g')
      .attr('class', 'line-group')
      .append('path')
      .attr('class', 'line')
      .style('fill', 'none')
      .attr('d', (d) => line(d.values))
      .style('stroke', (d, i) => color(i))
      .style('stroke-width', '3px');

    /* Add circles in the line */
    lines
      .selectAll('circle-group')
      .data(data)
      .enter()
      .append('g')
      .style('fill', (d, i) => color(i))
      .selectAll('circle')
      .data((d) => d.values)
      .enter()
      .append('g')
      .attr('class', 'circle')
      .on('mouseover', (d, i) => {
        if (data.length) {
          renderTooltip(d, i);
        }
      })
      .on('mouseout', () => {
        removeTooltip();
      })
      .append('circle')
      .attr('cx', (d) => xScale(d.x))
      .attr('cy', (d) => yScale(d.y))
      .attr('r', circleRadius)
      .on('mouseover', () => {
        d3.select(this)
          .transition()
          .duration(duration)
          .attr('r', circleRadiusHover);
      })
      .on('mouseout', () => {
        d3.select(this).transition().duration(duration).attr('r', circleRadius);
      });

    /* Add Axis into SVG */
    const xAxis = d3
      .axisBottom(xScale)
      .ticks(data[0].values.length > 5 ? data[0].values.length : 5);
    const yAxis = d3.axisLeft(yScale).ticks(5);

    svg
      .append('g')
      .attr('class', 'x axis')
      .attr('transform', `translate(0, ${height - margin})`)
      .call(xAxis);

    svg.append('g').attr('class', 'y axis').call(yAxis);
  }, [data, helpText]);

  useEffect(() => {
    draw();
  }, [count, draw]);

  useEffect(() => {
    function handleResize() {
      draw();
    }

    window.addEventListener('resize', handleResize);

    handleResize();

    return () => window.removeEventListener('resize', handleResize);
  }, [draw]);

  return <div id="chart" />;
}

export default LineChart;
