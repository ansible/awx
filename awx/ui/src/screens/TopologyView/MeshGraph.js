import React, { useEffect, useState } from 'react';
import { useHistory } from 'react-router-dom';
import styled from 'styled-components';
import debounce from 'util/debounce';
// import { t } from '@lingui/macro';
import * as d3 from 'd3';
import Legend from './Legend';
import Tooltip from './Tooltip';
import ContentLoading from './ContentLoading';
import {
  renderStateColor,
  renderLabelText,
  renderNodeType,
  renderNodeIcon,
  redirectToDetailsPage,
  getHeight,
  getWidth,
  // generateRandomNodes,
  // getRandomInt,
} from './utils/helpers';
import {
  MESH_FORCE_LAYOUT,
  DEFAULT_RADIUS,
  DEFAULT_NODE_COLOR,
  DEFAULT_NODE_HIGHLIGHT_COLOR,
  DEFAULT_NODE_LABEL_TEXT_COLOR,
  DEFAULT_FONT_SIZE,
  SELECTOR,
} from './constants';

const Loader = styled(ContentLoading)`
  height: 100%;
  position: absolute;
  width: 100%;
  background: white;
`;
function MeshGraph({ data, showLegend, zoom, setShowZoomControls }) {
  // function MeshGraph({ showLegend, zoom }) {
  const [isNodeSelected, setIsNodeSelected] = useState(false);
  const [selectedNode, setSelectedNode] = useState(null);
  const [nodeDetail, setNodeDetail] = useState(null);
  const history = useHistory();

  // const data = generateRandomNodes(getRandomInt(4, 50));
  const draw = () => {
    const width = getWidth(SELECTOR);
    const height = getHeight(SELECTOR);

    /* Add SVG */
    d3.selectAll(`#chart > svg`).remove();
    const svg = d3
      .select('#chart')
      .append('svg')
      .attr('class', 'mesh-svg')
      .attr('width', `${width}px`)
      .attr('height', `100%`);
    const mesh = svg.append('g').attr('class', 'mesh');

    const graph = data;

    const simulation = d3
      .forceSimulation()
      .nodes(graph.nodes)
      .force(
        'charge',
        d3.forceManyBody().strength(MESH_FORCE_LAYOUT.defaultForceStrength)
      )
      .force(
        'link',
        d3.forceLink(graph.links).id((d) => d.hostname)
      )
      .force(
        'collide',
        d3.forceCollide(MESH_FORCE_LAYOUT.defaultCollisionFactor)
      )
      .force('forceX', d3.forceX(MESH_FORCE_LAYOUT.defaultForceX))
      .force('forceY', d3.forceY(MESH_FORCE_LAYOUT.defaultForceY))
      .force('center', d3.forceCenter(width / 2, height / 2));

    const link = mesh
      .append('g')
      .attr('class', `links`)
      .attr('data-cy', 'links')
      .selectAll('line')
      .data(graph.links)
      .enter()
      .append('line')
      .attr('class', (_, i) => `link-${i}`)
      .attr('data-cy', (d) => `${d.source.hostname}-${d.target.hostname}`)
      .style('fill', 'none')
      .style('stroke', '#ccc')
      .style('stroke-width', '2px')
      .attr('pointer-events', 'none')
      .on('mouseover', function showPointer() {
        d3.select(this).transition().style('cursor', 'pointer');
      });

    const node = mesh
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
      })
      .on('mouseleave', (_, d) => {
        deselectSiblings(d);
      })
      .on('click', (_, d) => {
        setNodeDetail(d);
        highlightSelected(d);
      });

    // node circles
    node
      .append('circle')
      .attr('r', DEFAULT_RADIUS)
      .attr('class', (d) => d.node_type)
      .attr('class', (d) => `id-${d.id}`)
      .attr('fill', DEFAULT_NODE_COLOR)
      .attr('stroke', DEFAULT_NODE_LABEL_TEXT_COLOR);

    // node type labels
    node
      .append('text')
      .text((d) => renderNodeType(d.node_type))
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'central')
      .attr('fill', DEFAULT_NODE_LABEL_TEXT_COLOR);

    // node hostname labels
    const hostNames = node.append('g');
    hostNames
      .append('text')
      .text((d) => renderLabelText(d.node_state, d.hostname))
      .attr('class', 'placeholder')
      .attr('fill', DEFAULT_NODE_LABEL_TEXT_COLOR)
      .attr('text-anchor', 'middle')
      .attr('y', 40)
      .each(function calculateLabelWidth() {
        // eslint-disable-next-line react/no-this-in-sfc
        const bbox = this.getBBox();
        // eslint-disable-next-line react/no-this-in-sfc
        d3.select(this.parentNode)
          .append('rect')
          .attr('x', bbox.x)
          .attr('y', bbox.y)
          .attr('width', bbox.width)
          .attr('height', bbox.height)
          .attr('rx', 8)
          .attr('ry', 8)
          .style('fill', (d) => renderStateColor(d.node_state));
      });
    svg.selectAll('text.placeholder').remove();
    hostNames
      .append('text')
      .text((d) => renderLabelText(d.node_state, d.hostname))
      .attr('font-size', DEFAULT_FONT_SIZE)
      .attr('fill', DEFAULT_NODE_LABEL_TEXT_COLOR)
      .attr('text-anchor', 'middle')
      .attr('y', 38);

    simulation.nodes(graph.nodes).on('tick', ticked);
    simulation.force('link').links(graph.links);

    function ticked() {
      d3.select('.simulation-loader').style('visibility', 'visible');

      link
        .attr('x1', (d) => d.source.x)
        .attr('y1', (d) => d.source.y)
        .attr('x2', (d) => d.target.x)
        .attr('y2', (d) => d.target.y);

      node.attr('transform', (d) => `translate(${d.x},${d.y})`);
      calculateAlphaDecay(simulation.alpha(), simulation.alphaMin(), 20);
    }

    svg.call(zoom);

    function highlightSiblings(n) {
      setTimeout(() => {
        svg
          .select(`circle.id-${n.id}`)
          .attr('fill', DEFAULT_NODE_HIGHLIGHT_COLOR);
        const immediate = graph.links.filter(
          (l) =>
            n.hostname === l.source.hostname || n.hostname === l.target.hostname
        );
        immediate.forEach((s) => {
          svg
            .selectAll(`.link-${s.index}`)
            .transition()
            .style('stroke', '#0066CC')
            .style('stroke-width', '3px');
        });
      }, 0);
    }

    function deselectSiblings(n) {
      svg.select(`circle.id-${n.id}`).attr('fill', DEFAULT_NODE_COLOR);
      const immediate = graph.links.filter(
        (l) =>
          n.hostname === l.source.hostname || n.hostname === l.target.hostname
      );
      immediate.forEach((s) => {
        svg
          .selectAll(`.link-${s.index}`)
          .transition()
          .style('stroke', '#ccc')
          .style('stroke-width', '2px');
      });
    }

    function highlightSelected(n) {
      if (svg.select(`circle.id-${n.id}`).attr('stroke-width') !== null) {
        // toggle rings
        svg.select(`circle.id-${n.id}`).attr('stroke-width', null);
        // show default empty state of tooltip
        setIsNodeSelected(false);
        setSelectedNode(null);
        return;
      }
      svg.selectAll('circle').attr('stroke-width', null);
      svg
        .select(`circle.id-${n.id}`)
        .attr('stroke-width', '5px')
        .attr('stroke', '#D2D2D2');
      setIsNodeSelected(true);
      setSelectedNode(n);
    }

    function calculateAlphaDecay(a, aMin, x) {
      setShowZoomControls(false);
      const decayPercentage = Math.min((aMin / a) * 100);
      if (decayPercentage >= x) {
        d3.select('.simulation-loader').style('visibility', 'hidden');
        setShowZoomControls(true);
      }
    }
  };

  useEffect(() => {
    function handleResize() {
      d3.select('.simulation-loader').style('visibility', 'visible');
      setSelectedNode(null);
      setIsNodeSelected(false);
      draw();
    }
    window.addEventListener('resize', debounce(handleResize, 500));
    handleResize();
    return () => window.removeEventListener('resize', handleResize);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div id="chart" style={{ position: 'relative', height: '100%' }}>
      {showLegend && <Legend />}
      <Tooltip
        isNodeSelected={isNodeSelected}
        renderNodeIcon={renderNodeIcon(selectedNode)}
        nodeDetail={nodeDetail}
        redirectToDetailsPage={() =>
          redirectToDetailsPage(selectedNode, history)
        }
      />
      <Loader className="simulation-loader" />
    </div>
  );
}

export default MeshGraph;
