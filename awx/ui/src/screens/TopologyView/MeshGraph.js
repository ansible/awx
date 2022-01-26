import React, { useCallback, useEffect } from 'react';
import debounce from 'util/debounce';
// import { t } from '@lingui/macro';
import * as d3 from 'd3';

// function MeshGraph({ data }) {
function MeshGraph({ redirectToDetailsPage }) {
  const draw = useCallback(() => {
    const data = {
      nodes: [
        {
          id: 1,
          hostname: 'awx_1',
          node_type: 'hybrid',
          node_state: 'healthy',
        },
        {
          id: 3,
          hostname: 'receptor-1',
          node_type: 'execution',
          node_state: 'healthy',
        },
        {
          id: 4,
          hostname: 'receptor-2',
          node_type: 'execution',
          node_state: 'healthy',
        },
        {
          id: 2,
          hostname: 'receptor-hop',
          node_type: 'hop',
          node_state: 'healthy',
        },
        {
          id: 5,
          hostname: 'receptor-hop-1',
          node_type: 'hop',
          node_state: 'healthy',
        },
        {
          id: 6,
          hostname: 'receptor-hop-2',
          node_type: 'hop',
          node_state: 'healthy',
        },
        {
          id: 7,
          hostname: 'receptor-hop-3',
          node_type: 'hop',
          node_state: 'healthy',
        },
        {
          id: 8,
          hostname: 'receptor-hop-4',
          node_type: 'hop',
          node_state: 'healthy',
        },
      ],
      links: [
        {
          source: 'receptor-hop',
          target: 'awx_1',
        },
        {
          source: 'receptor-1',
          target: 'receptor-hop',
        },
        {
          source: 'receptor-2',
          target: 'receptor-hop',
        },
        {
          source: 'receptor-hop-3',
          target: 'receptor-hop',
        },
        // {
        //   "source": "receptor-2",
        //   "target": "receptor-hop-1"
        // },
        // {
        //   "source": "receptor-2",
        //   "target": "receptor-hop-2"
        // }
      ],
    };
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
      // .scaleExtent([1, 8])
      .on('zoom', (event) => {
        svg.attr('transform', event.transform);
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

    const graph = data;

    const simulation = d3
      .forceSimulation()
      .force('charge', d3.forceManyBody(75).strength(-100))
      .force(
        'link',
        d3.forceLink().id((d) => d.hostname)
      )
      .force('collide', d3.forceCollide(80))
      .force('forceX', d3.forceX(0))
      .force('forceY', d3.forceY(0))
      .force('center', d3.forceCenter(width / 2, height / 2));

    // const simulation = d3
    //   .forceSimulation()
    //   .force(
    //     'link',
    //     d3.forceLink().id((d) => d.hostname)
    //   )
    //   .force('charge', d3.forceManyBody().strength(-350))
    //   .force(
    //     'collide',
    //     d3.forceCollide((d) =>
    //       d.node_type === 'execution' || d.node_type === 'hop' ? 75 : 100
    //     )
    //   )
    //   .force('center', d3.forceCenter(width / 2, height / 2));

    const link = svg
      .append('g')
      .attr('class', `links`)
      .attr('data-cy', 'links')
      // .selectAll('path')
      .selectAll('line')
      .data(graph.links)
      .enter()
      .append('line')
      // .append('path')
      .attr('class', (d, i) => `link-${i}`)
      .attr('data-cy', (d) => `${d.source}-${d.target}`)
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
      .attr('data-cy', 'nodes')
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
      .attr('fill', (d) => renderNodeColor(d.node_type))
      .attr('stroke', 'white');
    svg.call(expandGlow);

    // legend
    svg.append('text').attr('x', 10).attr('y', 20).text('Legend');

    svg
      .append('g')
      .selectAll('g')
      .attr('class', 'chart-legend')
      .attr('data-cy', 'chart-legend')
      .data(graph.nodes)
      .enter()
      .append('circle')
      .attr('cx', 10)
      .attr('cy', (d, i) => 50 + i * 25)
      .attr('r', defaultRadius)
      .attr('class', (d) => d.node_type)
      .style('fill', (d) => renderNodeColor(d.node_type));

    // legend text
    svg
      .append('g')
      .attr('class', 'chart-text')
      .attr('data-cy', 'chart-text')
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
      .attr('data-cy', 'd3-tooltip')
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
      // link.attr('d', linkArc);
      link
        .attr('x1', (d) => d.source.x)
        .attr('y1', (d) => d.source.y)
        .attr('x2', (d) => d.target.x)
        .attr('y2', (d) => d.target.y);

      node.attr('transform', (d) => `translate(${d.x},${d.y})`);
    }

    // function linkArc(d) {
    //   const dx = d.target.x - d.source.x;
    //   const dy = d.target.y - d.source.y;
    //   const dr = Math.sqrt(dx * dx + dy * dy);
    //   return `M${d.source.x},${d.source.y}A${dr},${dr} 0 0,1 ${d.target.x},${d.target.y}`;
    // }

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

    function renderNodeColor(nodeType) {
      const colorKey = {
        hop: '#C46100',
        execution: '#F0AB00',
        hybrid: '#0066CC',
        control: '#005F60',
      };

      return colorKey[nodeType];
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
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    function handleResize() {
      draw();
    }

    window.addEventListener('resize', debounce(handleResize, 500));
    draw();
    return () => window.removeEventListener('resize', handleResize);
  }, [draw]);

  return <div id="chart" />;
}

export default MeshGraph;
