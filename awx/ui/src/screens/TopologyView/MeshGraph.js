import React, { useEffect, useCallback } from 'react';
import debounce from 'util/debounce';
import { useHistory } from 'react-router-dom';
// import { t } from '@lingui/macro';
import { InstancesAPI } from 'api';
import * as d3 from 'd3';

function MeshGraph({ data }) {
  // function MeshGraph() {
  // const data = {
  //   nodes: [
  //     {
  //       hostname: 'aapc1.local',
  //       node_state: 'healthy',
  //       node_type: 'control',
  //       id: 1,
  //     },
  //     {
  //       hostname: 'aapc2.local',
  //       node_type: 'control',
  //       node_state: 'disabled',
  //       id: 2,
  //     },
  //     {
  //       hostname: 'aapc3.local',
  //       node_type: 'control',
  //       node_state: 'healthy',
  //       id: 3,
  //     },
  //     {
  //       hostname: 'aape1.local',
  //       node_type: 'execution',
  //       node_state: 'error',
  //       id: 4,
  //     },
  //     {
  //       hostname: 'aape2.local',
  //       node_type: 'execution',
  //       node_state: 'error',
  //       id: 5,
  //     },
  //     {
  //       hostname: 'aape3.local',
  //       node_type: 'execution',
  //       node_state: 'healthy',
  //       id: 6,
  //     },
  //     {
  //       hostname: 'aape4.local',
  //       node_type: 'execution',
  //       node_state: 'healthy',
  //       id: 7,
  //     },
  //     {
  //       hostname: 'aaph1.local',
  //       node_type: 'hop',
  //       node_state: 'disabled',
  //       id: 8,
  //     },
  //     {
  //       hostname: 'aaph2.local',
  //       node_type: 'hop',
  //       node_state: 'healthy',
  //       id: 9,
  //     },
  //     {
  //       hostname: 'aaph3.local',
  //       node_type: 'hop',
  //       node_state: 'error',
  //       id: 10,
  //     },
  //   ],
  //   links: [
  //     { source: 'aapc1.local', target: 'aapc2.local' },
  //     { source: 'aapc1.local', target: 'aapc3.local' },
  //     { source: 'aapc1.local', target: 'aape1.local' },
  //     { source: 'aapc1.local', target: 'aape2.local' },

  //     { source: 'aapc2.local', target: 'aapc3.local' },
  //     { source: 'aapc2.local', target: 'aape1.local' },
  //     { source: 'aapc2.local', target: 'aape2.local' },

  //     { source: 'aapc3.local', target: 'aape1.local' },
  //     { source: 'aapc3.local', target: 'aape2.local' },

  //     { source: 'aape3.local', target: 'aaph1.local' },
  //     { source: 'aape3.local', target: 'aaph2.local' },

  //     { source: 'aape4.local', target: 'aaph3.local' },

  //     { source: 'aaph1.local', target: 'aapc1.local' },
  //     { source: 'aaph1.local', target: 'aapc2.local' },
  //     { source: 'aaph1.local', target: 'aapc3.local' },

  //     { source: 'aaph2.local', target: 'aapc1.local' },
  //     { source: 'aaph2.local', target: 'aapc2.local' },
  //     { source: 'aaph2.local', target: 'aapc3.local' },

  //     { source: 'aaph3.local', target: 'aaph1.local' },
  //     { source: 'aaph3.local', target: 'aaph2.local' },
  //   ],
  // };
  const history = useHistory();
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
    const defaultRadius = 6;
    const highlightRadius = 9;

    const zoom = d3
      .zoom()
      .scaleExtent([1, 8])
      .on('zoom', (event) => {
        svg.selectAll('.links, .nodes').attr('transform', event.transform);
      });

    /* Add SVG */
    d3.selectAll(`#chart > *`).remove();

    const svg = d3
      .select('#chart')
      .append('svg')
      .attr('width', `${width + margin}px`)
      .attr('height', `${height + margin}px`)
      .append('g')
      .attr('transform', `translate(${margin}, ${margin})`)
      .call(zoom);

    const color = d3.scaleOrdinal(d3.schemeCategory10);
    const graph = data;

    const simulation = d3
      .forceSimulation()
      .force(
        'link',
        d3.forceLink().id((d) => d.hostname)
      )
      .force('charge', d3.forceManyBody().strength(-350))
      .force(
        'collide',
        d3.forceCollide((d) =>
          d.node_type === 'execution' || d.node_type === 'hop' ? 75 : 100
        )
      )
      .force('center', d3.forceCenter(width / 2, height / 2));

    const link = svg
      .append('g')
      .attr('class', `links`)
      .selectAll('path')
      .data(graph.links)
      .enter()
      .append('path')
      .attr('class', (d, i) => `link-${i}`)
      .style('fill', 'none')
      .style('stroke', '#ccc')
      .style('stroke-width', '2px')
      .attr('pointer-events', 'none')
      .on('mouseover', function showPointer() {
        d3.select(this).transition().style('cursor', 'pointer');
      });

    const node = svg
      .append('g')
      .attr('class', 'nodes')
      .selectAll('g')
      .data(graph.nodes)
      .enter()
      .append('g')
      .on('mouseenter', function handleNodeHover(_, d) {
        d3.select(this).transition().style('cursor', 'pointer');
        highlightSiblings(d);
        tooltip
          .html(
            `<h3>Details</h3> <hr>name: ${d.hostname} <br>type: ${d.node_type} <br>status: ${d.node_state} <br> <a>Click on a node to view the details</a>`
          )
          .style('visibility', 'visible');
      })
      .on('mouseleave', (_, d) => {
        deselectSiblings(d);
        tooltip.html(``).style('visibility', 'hidden');
      })
      .on('click', (_, d) => {
        if (d.node_type !== 'hop') {
          redirectToDetailsPage(d);
        }
      });

    // health rings on nodes
    node
      .append('circle')
      .attr('r', 8)
      .attr('class', (d) => d.node_state)
      .attr('stroke', (d) => renderHealthColor(d.node_state))
      .attr('fill', (d) => renderHealthColor(d.node_state));

    // inner node ring
    node
      .append('circle')
      .attr('r', defaultRadius)
      .attr('class', (d) => d.node_type)
      .attr('class', (d) => `id-${d.id}`)
      .attr('fill', (d) => color(d.node_type))
      .attr('stroke', 'white');
    svg.call(expandGlow);

    // legend
    svg.append('text').attr('x', 10).attr('y', 20).text('Legend');

    svg
      .append('g')
      .selectAll('g')
      .attr('class', 'chart-legend')
      .data(graph.nodes)
      .enter()
      .append('circle')
      .attr('cx', 10)
      .attr('cy', (d, i) => 50 + i * 25)
      .attr('r', defaultRadius)
      .attr('class', (d) => d.node_type)
      .style('fill', (d) => color(d.node_type));

    // legend text
    svg
      .append('g')
      .attr('class', 'chart-text')
      .selectAll('g')
      .data(graph.nodes)
      .enter()
      .append('text')
      .attr('x', 20)
      .attr('y', (d, i) => 50 + i * 25)
      .text((d) => `${d.hostname} - ${d.node_type}`)
      .attr('text-anchor', 'left')
      .style('alignment-baseline', 'middle');

    const tooltip = d3
      .select('#chart')
      .append('div')
      .attr('class', 'd3-tooltip')
      .style('position', 'absolute')
      .style('top', '200px')
      .style('right', '40px')
      .style('z-index', '10')
      .style('visibility', 'hidden')
      .style('padding', '15px')
      // .style('border', '1px solid #e6e6e6')
      // .style('box-shadow', '5px 5px 5px #e6e6e6')
      .style('max-width', '15%')
      // .style('background', 'rgba(0,0,0,0.6)')
      // .style('border-radius', '5px')
      // .style('color', '#fff')
      .style('font-family', 'sans-serif')
      .style('color', '#e6e6e')
      .text('');

    // node labels
    node
      .append('text')
      .text((d) => d.hostname)
      .attr('x', 16)
      .attr('y', 3);

    simulation.nodes(graph.nodes).on('tick', ticked);
    simulation.force('link').links(graph.links);

    function ticked() {
      link.attr('d', linkArc);

      node.attr('transform', (d) => `translate(${d.x},${d.y})`);
    }

    function linkArc(d) {
      const dx = d.target.x - d.source.x;
      const dy = d.target.y - d.source.y;
      const dr = Math.sqrt(dx * dx + dy * dy);
      return `M${d.source.x},${d.source.y}A${dr},${dr} 0 0,1 ${d.target.x},${d.target.y}`;
    }

    function contractGlow() {
      svg
        .selectAll('.healthy')
        .transition()
        .duration(1000)
        .attr('stroke-width', '1px')
        .on('end', expandGlow);
    }

    function expandGlow() {
      svg
        .selectAll('.healthy')
        .transition()
        .duration(1000)
        .attr('stroke-width', '4.5px')
        .on('end', contractGlow);
    }

    function renderHealthColor(nodeState) {
      const colorKey = {
        disabled: '#c6c6c6',
        healthy: '#50D050',
        error: '#ff6766',
      };
      return colorKey[nodeState];
    }

    function highlightSiblings(n) {
      setTimeout(() => {
        svg.selectAll(`id-${n.id}`).attr('r', highlightRadius);
        const immediate = graph.links.filter(
          (l) =>
            n.hostname === l.source.hostname || n.hostname === l.target.hostname
        );
        immediate.forEach((s) => {
          svg
            .selectAll(`.link-${s.index}`)
            .transition()
            .style('stroke', '#6e6e6e');
          svg
            .selectAll(`.id-${s.source.id}`)
            .transition()
            .attr('r', highlightRadius);
          svg
            .selectAll(`.id-${s.target.id}`)
            .transition()
            .attr('r', highlightRadius);
        });
      }, 0);
    }

    function deselectSiblings(n) {
      svg.selectAll(`id-${n.id}`).attr('r', defaultRadius);
      const immediate = graph.links.filter(
        (l) =>
          n.hostname === l.source.hostname || n.hostname === l.target.hostname
      );
      immediate.forEach((s) => {
        svg.selectAll(`.link-${s.index}`).transition().style('stroke', '#ccc');
        svg
          .selectAll(`.id-${s.source.id}`)
          .transition()
          .attr('r', defaultRadius);
        svg
          .selectAll(`.id-${s.target.id}`)
          .transition()
          .attr('r', defaultRadius);
      });
    }

    async function redirectToDetailsPage({ id: nodeId }) {
      const {
        data: { results },
      } = await InstancesAPI.readInstanceGroup(nodeId);
      const { id: instanceGroupId } = results[0];
      const constructedURL = `/instance_groups/${instanceGroupId}/instances/${nodeId}/details`;
      history.push(constructedURL);
    }

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  useEffect(() => {
    function handleResize() {
      draw();
    }

    window.addEventListener('resize', debounce(handleResize, 500));

    handleResize();

    return () => window.removeEventListener('resize', handleResize);
  }, [draw]);

  return <div id="chart" />;
}

export default MeshGraph;
