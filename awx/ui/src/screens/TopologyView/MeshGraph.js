import React, { useEffect, useState } from 'react';
import { useHistory } from 'react-router-dom';
import styled from 'styled-components';
import debounce from 'util/debounce';
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
import webWorker from '../../util/webWorker';
import {
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
  const [simulationProgress, setSimulationProgress] = useState(null);
  const history = useHistory();

  // const data = generateRandomNodes(getRandomInt(4, 50));
  const draw = () => {
    setShowZoomControls(false);
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

    /* WEB WORKER */
    const worker = webWorker();
    worker.postMessage({
      nodes: graph.nodes,
      links: graph.links,
    });

    worker.onmessage = function handleWorkerEvent(event) {
      switch (event.data.type) {
        case 'tick':
          return ticked(event.data);
        case 'end':
          return ended(event.data);
        default:
          return false;
      }
    };

    function ticked({ progress }) {
      const calculatedPercent = Math.round(progress * 100);
      setSimulationProgress(calculatedPercent);
    }

    function ended({ nodes, links }) {
      // Remove loading screen
      d3.select('.simulation-loader').style('visibility', 'hidden');
      setShowZoomControls(true);
      // Center the mesh
      const simulation = d3
        .forceSimulation(nodes)
        .force('center', d3.forceCenter(width / 2, height / 2));
      simulation.tick();
      // Add links
      mesh
        .append('g')
        .attr('class', `links`)
        .attr('data-cy', 'links')
        .selectAll('line')
        .data(links)
        .enter()
        .append('line')
        .attr('x1', (d) => d.source.x)
        .attr('y1', (d) => d.source.y)
        .attr('x2', (d) => d.target.x)
        .attr('y2', (d) => d.target.y)
        .attr('class', (_, i) => `link-${i}`)
        .attr('data-cy', (d) => `${d.source.hostname}-${d.target.hostname}`)
        .style('fill', 'none')
        .style('stroke', '#ccc')
        .style('stroke-width', '2px')
        .attr('pointer-events', 'none')
        .on('mouseover', function showPointer() {
          d3.select(this).transition().style('cursor', 'pointer');
        });
      // add nodes
      const node = mesh
        .append('g')
        .attr('class', 'nodes')
        .attr('data-cy', 'nodes')
        .selectAll('g')
        .data(nodes)
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
        .attr('cx', (d) => d.x)
        .attr('cy', (d) => d.y)
        .attr('class', (d) => d.node_type)
        .attr('class', (d) => `id-${d.id}`)
        .attr('fill', DEFAULT_NODE_COLOR)
        .attr('stroke', DEFAULT_NODE_LABEL_TEXT_COLOR);

      // node type labels
      node
        .append('text')
        .text((d) => renderNodeType(d.node_type))
        .attr('x', (d) => d.x)
        .attr('y', (d) => d.y)
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'central')
        .attr('fill', DEFAULT_NODE_LABEL_TEXT_COLOR);

      // node hostname labels
      const hostNames = node.append('g');
      hostNames
        .append('text')
        .attr('x', (d) => d.x)
        .attr('y', (d) => d.y + 40)
        .text((d) => renderLabelText(d.node_state, d.hostname))
        .attr('class', 'placeholder')
        .attr('fill', DEFAULT_NODE_LABEL_TEXT_COLOR)
        .attr('text-anchor', 'middle')
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
        .attr('x', (d) => d.x)
        .attr('y', (d) => d.y + 38)
        .text((d) => renderLabelText(d.node_state, d.hostname))
        .attr('font-size', DEFAULT_FONT_SIZE)
        .attr('fill', DEFAULT_NODE_LABEL_TEXT_COLOR)
        .attr('text-anchor', 'middle');

      svg.call(zoom);

      function highlightSiblings(n) {
        svg
          .select(`circle.id-${n.id}`)
          .attr('fill', DEFAULT_NODE_HIGHLIGHT_COLOR);
        const immediate = links.filter(
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
      }

      function deselectSiblings(n) {
        svg.select(`circle.id-${n.id}`).attr('fill', DEFAULT_NODE_COLOR);
        const immediate = links.filter(
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
      <Loader className="simulation-loader" progress={simulationProgress} />
    </div>
  );
}

export default MeshGraph;
