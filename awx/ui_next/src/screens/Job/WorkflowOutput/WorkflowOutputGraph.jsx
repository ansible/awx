import 'styled-components/macro';
import React, { useContext, useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { WorkflowStateContext } from '../../../contexts/Workflow';
import {
  getScaleAndOffsetToFit,
  getTranslatePointsForZoom,
} from '../../../components/Workflow/WorkflowUtils';
import WorkflowOutputLink from './WorkflowOutputLink';
import WorkflowOutputNode from './WorkflowOutputNode';
import {
  WorkflowHelp,
  WorkflowLegend,
  WorkflowLinkHelp,
  WorkflowNodeHelp,
  WorkflowStartNode,
  WorkflowTools,
} from '../../../components/Workflow';

function WorkflowOutputGraph() {
  const [linkHelp, setLinkHelp] = useState();
  const [nodeHelp, setNodeHelp] = useState();
  const [zoomPercentage, setZoomPercentage] = useState(100);
  const svgRef = useRef(null);
  const gRef = useRef(null);

  const { links, nodePositions, nodes, showLegend, showTools } = useContext(
    WorkflowStateContext
  );

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
      {(nodeHelp || linkHelp) && (
        <WorkflowHelp>
          {nodeHelp && <WorkflowNodeHelp node={nodeHelp} />}
          {linkHelp && <WorkflowLinkHelp link={linkHelp} />}
        </WorkflowHelp>
      )}
      <svg
        id="workflow-svg"
        ref={svgRef}
        css="display: flex; height: 100%; background-color: #f6f6f6;"
      >
        <g id="workflow-g" ref={gRef}>
          {nodePositions && [
            <WorkflowStartNode key="start" showActionTooltip={false} />,
            links.map(link => (
              <WorkflowOutputLink
                key={`link-${link.source.id}-${link.target.id}`}
                link={link}
                mouseEnter={() => setLinkHelp(link)}
                mouseLeave={() => setLinkHelp(null)}
              />
            )),
            nodes.map(node => {
              if (node.id > 1) {
                return (
                  <WorkflowOutputNode
                    key={`node-${node.id}`}
                    mouseEnter={() => setNodeHelp(node)}
                    mouseLeave={() => setNodeHelp(null)}
                    node={node}
                  />
                );
              }
              return null;
            }),
          ]}
        </g>
      </svg>
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

export default WorkflowOutputGraph;
