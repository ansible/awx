import React, { Fragment, useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { arrayOf, bool, shape } from 'prop-types';
import { calcZoomAndFit, getZoomTranslate } from '@util/workflow';
import {
  WorkflowOutputLink,
  WorkflowOutputNode,
  WorkflowOutputStartNode,
} from '@screens/Job/WorkflowOutput';
import {
  WorkflowHelp,
  WorkflowKey,
  WorkflowNodeHelp,
  WorkflowTools,
} from '@components/Workflow';

function WorkflowOutputGraph({
  links,
  nodePositions,
  nodes,
  showKey,
  showTools,
}) {
  const [nodeHelp, setNodeHelp] = useState();
  const [zoomPercentage, setZoomPercentage] = useState(100);
  const svgRef = useRef(null);
  const gRef = useRef(null);

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
    const svgElement = document.getElementById('workflow-svg');
    const svgBoundingClientRect = svgElement.getBoundingClientRect();
    d3.select(svgRef.current).call(
      zoomRef.transform,
      d3.zoomIdentity
        .translate(0, svgBoundingClientRect.height / 2 - 30)
        .scale(1)
    );

    setZoomPercentage(100);
  };

  const handleZoomChange = newScale => {
    const [translateX, translateY] = getZoomTranslate(svgRef.current, newScale);

    d3.select(svgRef.current).call(
      zoomRef.transform,
      d3.zoomIdentity.translate(translateX, translateY).scale(newScale)
    );
    setZoomPercentage(newScale * 100);
  };

  const handleFitGraph = () => {
    const [scaleToFit, yTranslate] = calcZoomAndFit(
      gRef.current,
      svgRef.current
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
    const [scaleToFit, yTranslate] = calcZoomAndFit(
      gRef.current,
      svgRef.current
    );

    d3.select(svgRef.current).call(
      zoomRef.transform,
      d3.zoomIdentity.translate(0, yTranslate).scale(scaleToFit)
    );

    setZoomPercentage(scaleToFit * 100);
    // We only want this to run once (when the component mounts)
    // Including zoomRef.transform in the deps array will cause this to
    // run very frequently.
    // Discussion: https://github.com/facebook/create-react-app/issues/6880
    // and https://github.com/facebook/react/issues/15865 amongst others
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <Fragment>
      {nodeHelp && (
        <WorkflowHelp>
          <WorkflowNodeHelp node={nodeHelp} />
        </WorkflowHelp>
      )}
      <svg
        id="workflow-svg"
        ref={svgRef}
        css="display: flex; height: 100%; background-color: #f6f6f6;"
      >
        <g id="workflow-g" ref={gRef}>
          {nodePositions && [
            <WorkflowOutputStartNode
              key="start"
              nodePositions={nodePositions}
            />,
            links.map(link => (
              <WorkflowOutputLink
                key={`link-${link.source.id}-${link.target.id}`}
                link={link}
                nodePositions={nodePositions}
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
                    nodePositions={nodePositions}
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
        {showKey && <WorkflowKey />}
      </div>
    </Fragment>
  );
}

WorkflowOutputGraph.propTypes = {
  links: arrayOf(shape()).isRequired,
  nodePositions: shape().isRequired,
  nodes: arrayOf(shape()).isRequired,
  showKey: bool.isRequired,
  showTools: bool.isRequired,
};

export default WorkflowOutputGraph;
