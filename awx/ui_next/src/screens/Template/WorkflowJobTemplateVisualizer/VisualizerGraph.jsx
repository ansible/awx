import React, { Fragment, useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { calcZoomAndFit } from '@util/workflow';
import {
  WorkflowHelp,
  WorkflowLinkHelp,
  WorkflowNodeHelp,
} from '@components/Workflow';
import {
  VisualizerLink,
  VisualizerNode,
  VisualizerStartNode,
} from '@screens/Template/WorkflowJobTemplateVisualizer';

function VizualizerGraph({
  links,
  nodes,
  readOnly,
  nodePositions,
  onDeleteNodeClick,
}) {
  const [helpText, setHelpText] = useState(null);
  const [nodeHelp, setNodeHelp] = useState();
  const [linkHelp, setLinkHelp] = useState();
  const svgRef = useRef(null);
  const gRef = useRef(null);

  // This is the zoom function called by using the mousewheel/click and drag
  const zoom = () => {
    const translation = [d3.event.transform.x, d3.event.transform.y];
    d3.select(gRef.current).attr(
      'transform',
      `translate(${translation}) scale(${d3.event.transform.k})`
    );
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
    const [scaleToFit, yTranslate] = calcZoomAndFit(gRef.current);

    d3.select(svgRef.current).call(
      zoomRef.transform,
      d3.zoomIdentity.translate(0, yTranslate).scale(scaleToFit)
    );
    // We only want this to run once (when the component mounts)
    // Including zoomRef.transform in the deps array will cause this to
    // run very frequently.
    // Discussion: https://github.com/facebook/create-react-app/issues/6880
    // and https://github.com/facebook/react/issues/15865 amongst others
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <Fragment>
      {(helpText || nodeHelp || linkHelp) && (
        <WorkflowHelp>
          {helpText && <p>{helpText}</p>}
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
            <VisualizerStartNode
              key="start"
              nodePositions={nodePositions}
              readOnly={readOnly}
              updateHelpText={setHelpText}
            />,
            links.map(link => (
              <VisualizerLink
                key={`link-${link.source.id}-${link.target.id}`}
                link={link}
                nodePositions={nodePositions}
                updateHelpText={setHelpText}
                updateLinkHelp={setLinkHelp}
                readOnly={readOnly}
              />
            )),
            nodes.map(node => {
              if (node.id > 1) {
                return (
                  <VisualizerNode
                    key={`node-${node.id}`}
                    node={node}
                    nodePositions={nodePositions}
                    updateHelpText={setHelpText}
                    updateNodeHelp={setNodeHelp}
                    readOnly={readOnly}
                    onDeleteNodeClick={onDeleteNodeClick}
                  />
                );
              }
              return null;
            }),
          ]}
        </g>
      </svg>
    </Fragment>
  );
}

export default VizualizerGraph;
