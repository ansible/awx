import React, { useEffect, useCallback } from 'react';
import { t } from '@lingui/macro';
import * as d3 from 'd3';

function MeshGraph({ data }) {
  console.log('data', data);
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
    const height = 600;

    /* Add SVG */
    d3.selectAll(`#chart > *`).remove();

    const svg = d3
      .select('#chart')
      .append('svg')
      .attr('width', `${width + margin}px`)
      .attr('height', `${height + margin}px`)
      .append('g')
      .attr('transform', `translate(${margin}, ${margin})`);

    const color = d3.scaleOrdinal(d3.schemeCategory10);

    const simulation = d3
      .forceSimulation()
      .force(
        'link',
        d3.forceLink().id(function (d) {
          return d.hostname;
        })
      )
      .force('charge', d3.forceManyBody().strength(-350))
      .force(
        'collide',
        d3.forceCollide(function (d) {
          return d.node_type === 'execution' || d.node_type === 'hop'
            ? 75
            : 100;
        })
      )
      .force('center', d3.forceCenter(width / 2, height / 2));

    const graph = data;

    const link = svg
      .append('g')
      .attr('class', 'links')
      .selectAll('path')
      .data(graph.links)
      .enter()
      .append('path')
      .style('fill', 'none')
      .style('stroke', '#ccc')
      .style('stroke-width', '2px')
      .attr('pointer-events', 'visibleStroke')
      .on('mouseover', function (event, d) {
        tooltip
          .html(`source: ${d.source.hostname} <br>target: ${d.target.hostname}`)
          .style('visibility', 'visible');
        d3.select(this).transition().style('cursor', 'pointer');
      })
      .on('mousemove', function () {
        tooltip
          .style('top', event.pageY - 10 + 'px')
          .style('left', event.pageX + 10 + 'px');
      })
      .on('mouseout', function () {
        tooltip.html(``).style('visibility', 'hidden');
      });

    const node = svg
      .append('g')
      .attr('class', 'nodes')
      .selectAll('g')
      .data(graph.nodes)
      .enter()
      .append('g')
      .on('mouseover', function (event, d) {
        tooltip
          .html(
            `name: ${d.hostname} <br>type: ${d.node_type} <br>status: ${d.node_state}`
          )
          .style('visibility', 'visible');
        // d3.select(this).transition().attr('r', 9).style('cursor', 'pointer');
      })
      .on('mousemove', function () {
        tooltip
          .style('top', event.pageY - 10 + 'px')
          .style('left', event.pageX + 10 + 'px');
      })
      .on('mouseout', function () {
        tooltip.html(``).style('visibility', 'hidden');
        // d3.select(this).attr('r', 6);
      });
    
    const healthRings = node
      .append('circle')
      .attr('r', 8)
      .attr('class', (d) => d.node_state)
      .attr('stroke', d => d.node_state === 'disabled' ? '#c6c6c6' : '#50D050')
      .attr('fill', d => d.node_state === 'disabled' ? '#c6c6c6' : '#50D050');
    
    const nodeRings = node
      .append('circle')
      .attr('r', 6)
      .attr('class', (d) => d.node_type)
      .attr('fill', function (d) {
        return color(d.node_type);
      });
    svg.call(expandGlow);

    const legend = svg
      .append('g')
      .attr('class', 'chart-legend')
      .selectAll('g')
      .data(graph.nodes)
      .enter()
      .append('circle')
      .attr('cx', 10)
      .attr('cy', function (d, i) {
        return 100 + i * 25;
      })
      .attr('r', 7)
      .attr('class', (d) => d.node_type)
      .style('fill', function (d) {
        return color(d.node_type);
      });

    const legend_text = svg
      .append('g')
      .attr('class', 'chart-text')
      .selectAll('g')
      .data(graph.nodes)
      .enter()
      .append('text')
      .attr('x', 20)
      .attr('y', function (d, i) {
        return 100 + i * 25;
      })
      .text((d) => `${d.hostname} - ${d.node_type}`)
      .attr('text-anchor', 'left')
      .style('alignment-baseline', 'middle');

    const tooltip = d3
      .select('#chart')
      .append('div')
      .attr('class', 'd3-tooltip')
      .style('position', 'absolute')
      .style('z-index', '10')
      .style('visibility', 'hidden')
      .style('padding', '15px')
      .style('background', 'rgba(0,0,0,0.6)')
      .style('border-radius', '5px')
      .style('color', '#fff')
      .style('font-family', 'sans-serif')
      .text('a simple tooltip');

    const labels = node
      .append('text')
      .text(function (d) {
        return d.hostname;
      })
      .attr('x', 16)
      .attr('y', 3);

    simulation.nodes(graph.nodes).on('tick', ticked);
    simulation.force('link').links(graph.links);

    function ticked() {
      link.attr('d', linkArc);
      node.attr('transform', function (d) {
        return 'translate(' + d.x + ',' + d.y + ')';
      });
    }

    function linkArc(d) {
      var dx = d.target.x - d.source.x,
        dy = d.target.y - d.source.y,
        dr = Math.sqrt(dx * dx + dy * dy);
      return (
        'M' +
        d.source.x +
        ',' +
        d.source.y +
        'A' +
        dr +
        ',' +
        dr +
        ' 0 0,1 ' +
        d.target.x +
        ',' +
        d.target.y
      );
    }

    function contractGlow() {
      healthRings
        .transition()
        .duration(1000)
        .attr('stroke-width', '1px')
        .on('end', expandGlow);
    }

    function expandGlow() {
      healthRings
        .transition()
        .duration(1000)
        .attr('stroke-width', '4.5px')
        .on('end', contractGlow);
    }

    const zoom = d3
      .zoom()
      .scaleExtent([1, 8])
      .on('zoom', function (event) {
        svg.selectAll('.links, .nodes').attr('transform', event.transform);
      });

    svg.call(zoom);
  }, [data]);

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

export default MeshGraph;
