import React, { useEffect, useState, useCallback } from 'react';
import { useHistory } from 'react-router-dom';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import debounce from 'util/debounce';
import * as d3 from 'd3';
import { InstancesAPI } from 'api';
import useRequest, { useDismissableError } from 'hooks/useRequest';
import AlertModal from 'components/AlertModal';
import ErrorDetail from 'components/ErrorDetail';
import Legend from './Legend';
import Tooltip from './Tooltip';
import ContentLoading from './ContentLoading';
import {
  renderStateColor,
  renderLinkStatusColor,
  renderLabelText,
  renderNodeType,
  renderNodeIcon,
  renderLinkState,
  renderLabelIcons,
  renderIconPosition,
  redirectToDetailsPage,
  getHeight,
  getWidth,
} from './utils/helpers';
import webWorker from '../../util/webWorker';
import {
  DEFAULT_RADIUS,
  DEFAULT_NODE_COLOR,
  DEFAULT_NODE_HIGHLIGHT_COLOR,
  DEFAULT_NODE_SYMBOL_TEXT_COLOR,
  DEFAULT_NODE_STROKE_COLOR,
  DEFAULT_FONT_SIZE,
  SELECTOR,
} from './constants';

const Loader = styled(ContentLoading)`
  height: 100%;
  position: absolute;
  width: 100%;
  background: white;
`;
function MeshGraph({
  data,
  showLegend,
  zoom,
  setShowZoomControls,
  storedNodes,
}) {
  const [isNodeSelected, setIsNodeSelected] = useState(false);
  const [selectedNode, setSelectedNode] = useState(null);
  const [simulationProgress, setSimulationProgress] = useState(null);
  const history = useHistory();
  const {
    result: { instance = {}, instanceGroups },
    error: fetchError,
    isLoading,
    request: fetchDetails,
  } = useRequest(
    useCallback(async () => {
      const { data: instanceData } = await InstancesAPI.readDetail(
        selectedNode.id
      );
      const { data: instanceGroupsData } = await InstancesAPI.readInstanceGroup(
        selectedNode.id
      );
      return {
        instance: instanceData,
        instanceGroups: instanceGroupsData,
      };
    }, [selectedNode]),
    {
      result: {},
    }
  );
  const { error: fetchInstanceError, dismissError } =
    useDismissableError(fetchError);

  useEffect(() => {
    if (selectedNode) {
      fetchDetails();
    }
  }, [selectedNode, fetchDetails]);

  function updateNodeSVG(nodes) {
    if (nodes) {
      d3.selectAll('[class*="id-"]')
        .data(nodes)
        .attr('stroke-dasharray', (d) => (d.enabled ? `1 0` : `5`));
    }
  }

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

  // update mesh when user toggles enabled/disabled slider
  useEffect(() => {
    if (instance?.id) {
      const updatedNodes = storedNodes.current.map((n) =>
        n.id === instance.id ? { ...n, enabled: instance.enabled } : n
      );
      storedNodes.current = updatedNodes;
      updateNodeSVG(storedNodes.current);
    }
  }, [instance]); // eslint-disable-line react-hooks/exhaustive-deps

  const draw = () => {
    let width;
    let height;
    setShowZoomControls(false);
    try {
      width = getWidth(SELECTOR);
      height = getHeight(SELECTOR);
    } catch (error) {
      width = 700;
      height = 600;
    }

    /* Add SVG */
    d3.selectAll(`#chart > svg`).remove();
    const svg = d3
      .select('#chart')
      .append('svg')
      .attr('aria-label', 'mesh-svg')
      .attr('class', 'mesh-svg')
      .attr('width', `${width}px`)
      .attr('height', `100%`);
    const mesh = svg.append('g').attr('class', 'mesh');

    const graph = data;
    if (storedNodes?.current) {
      graph.nodes = storedNodes.current;
    }

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
      // build the arrow.
      mesh
        .append('defs')
        .selectAll('marker')
        .data(['end', 'end-active', 'end-adding', 'end-removing'])
        .join('marker')
        .attr('id', String)
        .attr('viewBox', '0 -5 10 10')
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-5L10,0L0,5');
      mesh.select('#end').attr('refX', 23).attr('fill', '#6A6E73');
      mesh.select('#end-removing').attr('refX', 23).attr('fill', '#C9190B');
      mesh.select('#end-adding').attr('refX', 23).attr('fill', '#3E8635');
      mesh.select('#end-active').attr('refX', 18).attr('fill', '#0066CC');

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
        .attr('marker-end', (d) => {
          if (d.link_state === 'adding') {
            return 'url(#end-adding)';
          }
          if (d.link_state === 'removing') {
            return 'url(#end-removing)';
          }
          return 'url(#end)';
        })
        .attr('class', (_, i) => `link-${i}`)
        .attr('data-cy', (d) => `${d.source.hostname}-${d.target.hostname}`)
        .style('fill', 'none')
        .style('stroke', (d) => renderLinkStatusColor(d.link_state))
        .style('stroke-width', '2px')
        .style('stroke-dasharray', (d) => renderLinkState(d.link_state))
        .attr('pointer-events', 'none')
        .on('mouseover', function showPointer() {
          d3.select(this).style('cursor', 'pointer');
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
        .attr('data-cy', (d) => `node-${d.id}`)
        .on('mouseenter', function handleNodeHover(_, d) {
          d3.select(this).style('cursor', 'pointer');
          highlightSiblings(d);
        })
        .on('mouseleave', (_, d) => {
          deselectSiblings(d);
        })
        .on('click', (_, d) => {
          highlightSelected(d);
        });

      // node circles
      const nodeCircles = node.append('g');
      nodeCircles
        .append('circle')
        .attr('r', DEFAULT_RADIUS)
        .attr('cx', (d) => d.x)
        .attr('cy', (d) => d.y)
        .attr('class', (d) => d.node_type)
        .attr('class', (d) => `id-${d.id}`)
        .attr('fill', DEFAULT_NODE_COLOR)
        .attr('stroke-dasharray', (d) => (d.enabled ? `1 0` : `5`))
        .attr('stroke', (d) => renderStateColor(d.node_state));

      // node type labels
      node
        .append('text')
        .text((d) => renderNodeType(d.node_type))
        .attr('x', (d) => d.x)
        .attr('y', (d) => d.y)
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'central')
        .attr('fill', DEFAULT_NODE_SYMBOL_TEXT_COLOR);

      // node hostname labels
      const hostNames = node.append('g').attr('class', 'node-state-label');
      hostNames
        .append('text')
        .attr('x', (d) => d.x)
        .attr('y', (d) => d.y + 40)
        .text((d) => renderLabelText(d.node_state, d.hostname))
        .attr('class', 'placeholder')
        .attr('fill', 'white')
        .attr('text-anchor', 'middle')
        .each(function calculateLabelWidth() {
          // eslint-disable-next-line react/no-this-in-sfc
          const bbox = this.getBBox();
          const padding = 10;
          // eslint-disable-next-line react/no-this-in-sfc
          d3.select(this.parentNode)
            .append('rect')
            .attr('x', bbox.x - padding / 2)
            .attr('y', bbox.y)
            .attr('width', bbox.width + padding)
            .attr('height', bbox.height)
            .style('stroke-width', 1)
            .attr('rx', 4)
            .attr('ry', 4)
            .attr('fill', 'white')
            .style('stroke', DEFAULT_NODE_STROKE_COLOR);
        });
      svg.selectAll('text.placeholder').remove();
      hostNames
        .append('text')
        .attr('x', (d) => d.x)
        .attr('y', (d) => d.y + 38)
        .text((d) => renderLabelText(d.node_state, d.hostname))
        .attr('font-size', DEFAULT_FONT_SIZE)
        .attr('fill', 'black')
        .attr('text-anchor', 'middle');

      // add badge icons
      const badges = nodeCircles.append('g').attr('class', 'node-state-badge');
      badges.each(function drawStateBadge() {
        // eslint-disable-next-line react/no-this-in-sfc
        const bbox = this.parentNode.getBBox();
        // eslint-disable-next-line react/no-this-in-sfc
        d3.select(this)
          .append('circle')
          .attr('r', 9)
          .attr('cx', bbox.x)
          .attr('cy', bbox.y)
          .attr('fill', (d) => renderStateColor(d.node_state));
        d3.select(this)
          .append('path')
          .attr('class', (d) => `icon-${d.node_state}`)
          .attr('d', (d) => renderLabelIcons(d.node_state))
          .attr('transform', (d) => renderIconPosition(d.node_state, bbox))
          .attr('fill', 'white');
      });
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
            .style('stroke', '#0066CC')
            .style('stroke-width', '3px')
            .attr('marker-end', 'url(#end-active)');
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
            .style('stroke', (d) => renderLinkStatusColor(d.link_state))
            .style('stroke-width', '2px')
            .attr('marker-end', (d) => {
              if (d.link_state === 'adding') {
                return 'url(#end-adding)';
              }
              if (d.link_state === 'removing') {
                return 'url(#end-removing)';
              }
              return 'url(#end)';
            });
        });
      }

      function highlightSelected(n) {
        if (svg.select(`circle.id-${n.id}`).attr('stroke-width') !== null) {
          // toggle rings
          svg
            .select(`circle.id-${n.id}`)
            .attr('stroke', (d) => renderStateColor(d.node_state))
            .attr('stroke-width', null);
          // show default empty state of tooltip
          setIsNodeSelected(false);
          setSelectedNode(null);
          return;
        }
        svg
          .selectAll('circle')
          .attr('stroke', (d) => renderStateColor(d.node_state))
          .attr('stroke-width', null);
        svg
          .select(`circle.id-${n.id}`)
          .attr('stroke-width', '5px')
          .attr('stroke', '#0066CC');
        setIsNodeSelected(true);
        setSelectedNode(n);
      }
    }
  };

  return (
    <div id="chart" style={{ position: 'relative', height: '100%' }}>
      {showLegend && <Legend />}
      {instance && (
        <Tooltip
          isNodeSelected={isNodeSelected}
          renderNodeIcon={renderNodeIcon(selectedNode)}
          selectedNode={selectedNode}
          fetchInstance={fetchDetails}
          instanceGroups={instanceGroups}
          instanceDetail={instance}
          isLoading={isLoading}
          redirectToDetailsPage={() =>
            redirectToDetailsPage(selectedNode, history)
          }
        />
      )}
      <Loader className="simulation-loader" progress={simulationProgress} />
      {fetchInstanceError && (
        <AlertModal
          variant="error"
          title={t`Error!`}
          isOpen
          onClose={dismissError}
        >
          {t`Failed to get instance.`}
          <ErrorDetail error={fetchInstanceError} />
        </AlertModal>
      )}
    </div>
  );
}

export default MeshGraph;
