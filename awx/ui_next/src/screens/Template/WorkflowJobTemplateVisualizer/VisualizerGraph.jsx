import 'styled-components/macro';
import React, { useContext, useEffect, useRef, useState } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import { bool } from 'prop-types';
import * as d3 from 'd3';
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from '../../../contexts/Workflow';
import {
  getScaleAndOffsetToFit,
  constants as wfConstants,
  getTranslatePointsForZoom,
} from '../../../components/Workflow/WorkflowUtils';
import {
  WorkflowHelp,
  WorkflowLegend,
  WorkflowLinkHelp,
  WorkflowNodeHelp,
  WorkflowStartNode,
  WorkflowTools,
} from '../../../components/Workflow';
import VisualizerLink from './VisualizerLink';
import VisualizerNode from './VisualizerNode';

const PotentialLink = styled.polyline`
  pointer-events: none;
`;

const WorkflowSVG = styled.svg`
  background-color: #f6f6f6;
  display: flex;
  height: 100%;
`;

function VisualizerGraph({ i18n, readOnly }) {
  const [helpText, setHelpText] = useState(null);
  const [linkHelp, setLinkHelp] = useState();
  const [nodeHelp, setNodeHelp] = useState();
  const [zoomPercentage, setZoomPercentage] = useState(100);
  const svgRef = useRef(null);
  const gRef = useRef(null);

  const {
    addLinkSourceNode,
    addingLink,
    links,
    nodePositions,
    nodes,
    showLegend,
    showTools,
  } = useContext(WorkflowStateContext);

  const dispatch = useContext(WorkflowDispatchContext);

  const drawPotentialLinkToNode = node => {
    if (node.id !== addLinkSourceNode.id) {
      const sourceNodeX = nodePositions[addLinkSourceNode.id].x;
      const sourceNodeY =
        nodePositions[addLinkSourceNode.id].y - nodePositions[1].y;
      const targetNodeX = nodePositions[node.id].x;
      const targetNodeY = nodePositions[node.id].y - nodePositions[1].y;
      const startX = sourceNodeX + wfConstants.nodeW;
      const startY = sourceNodeY + wfConstants.nodeH / 2;
      const finishX = targetNodeX;
      const finishY = targetNodeY + wfConstants.nodeH / 2;

      d3.select('#workflow-potentialLink')
        .attr('points', `${startX},${startY} ${finishX},${finishY}`)
        .raise();
    }
  };

  const handleBackgroundClick = () => {
    setHelpText(null);
    dispatch({ type: 'CANCEL_LINK' });
  };

  const drawPotentialLinkToCursor = e => {
    const currentTransform = d3.zoomTransform(d3.select(gRef.current).node());
    const rect = e.target.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    const sourceNodeX = nodePositions[addLinkSourceNode.id].x;
    const sourceNodeY =
      nodePositions[addLinkSourceNode.id].y - nodePositions[1].y;
    const startX = sourceNodeX + wfConstants.nodeW;
    const startY = sourceNodeY + wfConstants.nodeH / 2;

    d3.select('#workflow-potentialLink')
      .attr(
        'points',
        `${startX},${startY} ${mouseX / currentTransform.k -
          currentTransform.x / currentTransform.k},${mouseY /
          currentTransform.k -
          currentTransform.y / currentTransform.k}`
      )
      .raise();
  };

  // This is the zoom function called by using the mousewheel/click and drag
  const zoom = () => {
    const translation = [d3.event.transform.x, d3.event.transform.y];
    d3.select(gRef.current).attr(
      'transform',
      `translate(${translation}) scale(${d3.event.transform.k})`
    );

    setZoomPercentage(d3.event.transform.k * 100);
  };

  const handlePan = direction => {
    const transform = d3.zoomTransform(d3.select(svgRef.current).node());

    let { x: xPos, y: yPos } = transform;
    const { k: currentScale } = transform;

    switch (direction) {
      case 'up':
        yPos -= 50;
        break;
      case 'down':
        yPos += 50;
        break;
      case 'left':
        xPos -= 50;
        break;
      case 'right':
        xPos += 50;
        break;
      default:
        // Throw an error?
        break;
    }

    d3.select(svgRef.current).call(
      zoomRef.transform,
      d3.zoomIdentity.translate(xPos, yPos).scale(currentScale)
    );
  };

  const handlePanToMiddle = () => {
    const svgBoundingClientRect = svgRef.current.getBoundingClientRect();
    d3.select(svgRef.current).call(
      zoomRef.transform,
      d3.zoomIdentity
        .translate(0, svgBoundingClientRect.height / 2 - 30)
        .scale(1)
    );

    setZoomPercentage(100);
  };

  const handleZoomChange = newScale => {
    const svgBoundingClientRect = svgRef.current.getBoundingClientRect();
    const currentScaleAndOffset = d3.zoomTransform(
      d3.select(svgRef.current).node()
    );

    const [translateX, translateY] = getTranslatePointsForZoom(
      svgBoundingClientRect,
      currentScaleAndOffset,
      newScale
    );

    d3.select(svgRef.current).call(
      zoomRef.transform,
      d3.zoomIdentity.translate(translateX, translateY).scale(newScale)
    );
    setZoomPercentage(newScale * 100);
  };

  const handleFitGraph = () => {
    const { k: currentScale } = d3.zoomTransform(
      d3.select(svgRef.current).node()
    );
    const gBoundingClientRect = d3
      .select(gRef.current)
      .node()
      .getBoundingClientRect();

    const gBBoxDimensions = d3
      .select(gRef.current)
      .node()
      .getBBox();

    const svgBoundingClientRect = svgRef.current.getBoundingClientRect();

    const [scaleToFit, yTranslate] = getScaleAndOffsetToFit(
      gBoundingClientRect,
      svgBoundingClientRect,
      gBBoxDimensions,
      currentScale
    );

    d3.select(svgRef.current).call(
      zoomRef.transform,
      d3.zoomIdentity.translate(0, yTranslate).scale(scaleToFit)
    );

    setZoomPercentage(scaleToFit * 100);
  };

  const zoomRef = d3
    .zoom()
    .scaleExtent([0.1, 2])
    .on('zoom', zoom);

  // Initialize the zoom
  useEffect(() => {
    d3.select(svgRef.current).call(zoomRef);
  }, [zoomRef]);

  // Attempt to zoom the graph to fit the available screen space
  useEffect(() => {
    handleFitGraph();
    // We only want this to run once (when the component mounts)
    // Including handleFitGraph in the deps array will cause this to
    // run very frequently.
    // Discussion: https://github.com/facebook/create-react-app/issues/6880
    // and https://github.com/facebook/react/issues/15865 amongst others
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <>
      {(helpText || nodeHelp || linkHelp) && (
        <WorkflowHelp>
          {helpText && <p>{helpText}</p>}
          {nodeHelp && <WorkflowNodeHelp node={nodeHelp} />}
          {linkHelp && <WorkflowLinkHelp link={linkHelp} />}
        </WorkflowHelp>
      )}
      <WorkflowSVG id="workflow-svg" ref={svgRef}>
        <defs>
          <marker
            className="WorkflowChart-noPointerEvents"
            id="workflow-triangle"
            markerHeight="6"
            markerUnits="strokeWidth"
            markerWidth="6"
            orient="auto"
            refX="10"
            viewBox="0 -5 10 10"
          >
            <path d="M0,-5L10,0L0,5" fill="#93969A" />
          </marker>
        </defs>
        <rect
          height="100%"
          id="workflow-backround"
          opacity="0"
          width="100%"
          {...(addingLink && {
            onMouseMove: e => drawPotentialLinkToCursor(e),
            onMouseOver: () =>
              setHelpText(
                i18n._(
                  t`Click an available node to create a new link.  Click outside the graph to cancel.`
                )
              ),
            onMouseOut: () => setHelpText(null),
            onClick: () => handleBackgroundClick(),
          })}
        />
        <g id="workflow-g" ref={gRef}>
          {nodePositions && [
            <WorkflowStartNode
              key="start"
              showActionTooltip={!readOnly}
              onUpdateHelpText={setHelpText}
              readOnly={readOnly}
            />,
            links.map(link => {
              if (
                nodePositions[link.source.id] &&
                nodePositions[link.target.id]
              ) {
                return (
                  <VisualizerLink
                    key={`link-${link.source.id}-${link.target.id}`}
                    link={link}
                    readOnly={readOnly}
                    updateLinkHelp={newLinkHelp => setLinkHelp(newLinkHelp)}
                    updateHelpText={newHelpText => setHelpText(newHelpText)}
                  />
                );
              }
              return null;
            }),
            nodes.map(node => {
              if (node.id > 1 && nodePositions[node.id] && !node.isDeleted) {
                return (
                  <VisualizerNode
                    key={`node-${node.id}`}
                    node={node}
                    readOnly={readOnly}
                    updateHelpText={newHelpText => setHelpText(newHelpText)}
                    updateNodeHelp={newNodeHelp => setNodeHelp(newNodeHelp)}
                    {...(addingLink && {
                      onMouseOver: () => drawPotentialLinkToNode(node),
                    })}
                  />
                );
              }
              return null;
            }),
          ]}
          {addingLink && (
            <PotentialLink
              id="workflow-potentialLink"
              markerEnd="url(#workflow-triangle)"
              stroke="#93969A"
              strokeDasharray="5,5"
              strokeWidth="2"
            />
          )}
        </g>
      </WorkflowSVG>
      <div css="position: absolute; top: 75px;right: 20px;display: flex;">
        {showTools && (
          <WorkflowTools
            onFitGraph={handleFitGraph}
            onPan={handlePan}
            onPanToMiddle={handlePanToMiddle}
            onZoomChange={handleZoomChange}
            zoomPercentage={zoomPercentage}
          />
        )}
        {showLegend && <WorkflowLegend />}
      </div>
    </>
  );
}

VisualizerGraph.propTypes = {
  readOnly: bool.isRequired,
};

export default withI18n()(VisualizerGraph);
