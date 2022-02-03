import React, { useEffect, useState } from 'react';
import { useHistory } from 'react-router-dom';
import { InstancesAPI } from 'api';
import debounce from 'util/debounce';
// import { t } from '@lingui/macro';
import * as d3 from 'd3';
import Legend from './Legend';
import Tooltip from './Tooltip';

// function MeshGraph({ data }) {
function MeshGraph({ showLegend }) {
  const [isNodeSelected, setIsNodeSelected] = useState(false);
  const [selectedNode, setSelectedNode] = useState(null);
  const [nodeDetail, setNodeDetail] = useState(null);
  const history = useHistory();

  function getRandomInt(min, max) {
    min = Math.ceil(min);
    max = Math.floor(max);
    return Math.floor(Math.random() * (max - min + 1)) + min;
  }
  let nodes = [];
  let links = [];
  const generateLinks = (n, r) => {
    for (let i = 0; i < r; i++) {
      const link = {
        source: n[getRandomInt(0, n.length - 1)].hostname,
        target: n[getRandomInt(0, n.length - 1)].hostname,
      };
      links.push(link);
    }
    return { nodes: n, links };
  };
  const generateNodes = (n) => {
    function getRandomType() {
      return ['hybrid', 'execution', 'control', 'hop'][getRandomInt(0, 3)];
    }
    function getRandomState() {
      return ['healthy', 'error', 'disabled'][getRandomInt(0, 2)];
    }
    for (let i = 0; i < n; i++) {
      const id = i + 1;
      const randomType = getRandomType();
      const randomState = getRandomState();
      const node = {
        id,
        hostname: `node-${id}`,
        node_type: randomType,
        node_state: randomState,
      };
      nodes.push(node);
    }
    return generateLinks(nodes, getRandomInt(1, n - 1));
  };
  const data = generateNodes(getRandomInt(5, 30));
  const draw = () => {
    const margin = 15;
    const defaultRadius = 16;
    const defaultCollisionFactor = 80;
    const defaultForceStrength = -100;
    const defaultForceBody = 75;
    const defaultForceX = 0;
    const defaultForceY = 0;
    const height = 600;
    const fallbackWidth = 700;
    const defaultNodeColor = '#0066CC';
    const defaultNodeHighlightColor = '#16407C';
    const defaultNodeLabelColor = 'white';
    const defaultFontSize = '12px';
    const getWidth = () => {
      let width;
      // This is in an a try/catch due to an error from jest.
      // Even though the d3.select returns a valid selector with
      // style function, it says it is null in the test
      try {
        width =
          parseInt(d3.select(`#chart`).style('width'), 10) - margin ||
          fallbackWidth;
      } catch (error) {
        width = fallbackWidth;
      }

      return width;
    };
    const width = getWidth();
    const zoom = d3.zoom().scaleExtent([-40, 40]).on('zoom', zoomed);

    /* Add SVG */
    d3.selectAll(`#chart > svg`).remove();

    const svg = d3
      .select('#chart')
      .append('svg')
      .attr('width', `${width + margin}px`)
      .attr('height', `${height + margin}px`)
      .attr('viewBox', [0, 0, width, height]);
    const mesh = svg
      .append('g')
      .attr('transform', `translate(${margin}, ${margin})`);

    const graph = data;

    const simulation = d3
      .forceSimulation()
      .force(
        'charge',
        d3.forceManyBody(defaultForceBody).strength(defaultForceStrength)
      )
      .force(
        'link',
        d3.forceLink().id((d) => d.hostname)
      )
      .force('collide', d3.forceCollide(defaultCollisionFactor))
      .force('forceX', d3.forceX(defaultForceX))
      .force('forceY', d3.forceY(defaultForceY))
      .force('center', d3.forceCenter(width / 2, height / 2));

    const link = mesh
      .append('g')
      .attr('class', `links`)
      .attr('data-cy', 'links')
      .selectAll('line')
      .data(graph.links)
      .enter()
      .append('line')
      .attr('class', (d, i) => `link-${i}`)
      .attr('data-cy', (d) => `${d.source}-${d.target}`)
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
      .attr('r', defaultRadius)
      .attr('class', (d) => d.node_type)
      .attr('class', (d) => `id-${d.id}`)
      .attr('fill', defaultNodeColor)
      .attr('stroke', defaultNodeLabelColor);

    // node type labels
    node
      .append('text')
      .text((d) => renderNodeType(d.node_type))
      .attr('text-anchor', 'middle')
      .attr('alignment-baseline', 'central')
      .attr('fill', defaultNodeLabelColor);

    // node hostname labels
    const hostNames = node.append('g');
    hostNames
      .append('text')
      .text((d) => renderLabelText(d.node_state, d.hostname))
      .attr('fill', defaultNodeLabelColor)
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

    hostNames
      .append('text')
      .text((d) => renderLabelText(d.node_state, d.hostname))
      .attr('font-size', defaultFontSize)
      .attr('fill', defaultNodeLabelColor)
      .attr('text-anchor', 'middle')
      .attr('y', 38);

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

    svg.call(zoom);

    function renderStateColor(nodeState) {
      const colorKey = {
        disabled: '#6A6E73',
        healthy: '#3E8635',
        error: '#C9190B',
      };
      return colorKey[nodeState];
    }
    function renderLabelText(nodeState, name) {
      const stateKey = {
        disabled: '\u25EF',
        healthy: '\u2713',
        error: '\u0021',
      };
      return `${stateKey[nodeState]}  ${name}`;
    }

    function renderNodeType(nodeType) {
      const typeKey = {
        hop: 'h',
        execution: 'Ex',
        hybrid: 'Hy',
        control: 'C',
      };

      return typeKey[nodeType];
    }

    function highlightSiblings(n) {
      setTimeout(() => {
        svg.select(`circle.id-${n.id}`).attr('fill', defaultNodeHighlightColor);
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
      svg.select(`circle.id-${n.id}`).attr('fill', defaultNodeColor);
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

    function zoomed({ transform }) {
      mesh.attr('transform', transform);
    }
  };

  async function redirectToDetailsPage() {
    const { id: nodeId } = selectedNode;
    const {
      data: { results },
    } = await InstancesAPI.readInstanceGroup(nodeId);
    const { id: instanceGroupId } = results[0];
    const constructedURL = `/instance_groups/${instanceGroupId}/instances/${nodeId}/details`;
    history.push(constructedURL);
  }

  function renderNodeIcon() {
    if (selectedNode) {
      const { node_type: nodeType } = selectedNode;
      const typeKey = {
        hop: 'h',
        execution: 'Ex',
        hybrid: 'Hy',
        control: 'C',
      };

      return typeKey[nodeType];
    }

    return false;
  }
  useEffect(() => {
    function handleResize() {
      draw();
    }
    window.addEventListener('resize', debounce(handleResize, 500));
    handleResize();
    return () => window.removeEventListener('resize', handleResize);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div id="chart" style={{ position: 'relative' }}>
      {showLegend && <Legend />}
      <Tooltip
        isNodeSelected={isNodeSelected}
        renderNodeIcon={renderNodeIcon}
        nodeDetail={nodeDetail}
        redirectToDetailsPage={redirectToDetailsPage}
      />
    </div>
  );
}

export default MeshGraph;
