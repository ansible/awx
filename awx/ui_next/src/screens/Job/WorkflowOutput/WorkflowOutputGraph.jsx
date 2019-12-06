import React, { Fragment, useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { WorkflowHelp, WorkflowHelpDetails } from '@components/Workflow';
import { secondsToHHMMSS } from '@util/dates';
import { calcZoomAndFit, constants as wfConstants, drawLinkLine, drawNodeTypeLetter, drawRootNode, enterLinks, enterNodes, layoutGraph } from '@util/workflow';
import { JOB_TYPE_URL_SEGMENTS } from '../../../constants';

function Graph({
  links,
  nodes,
}) {
  const [helpText, setHelpText] = useState();
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

  // Draw the graph - this will get triggered whenever
  // nodes or links changes
  useEffect(() => {
    const nodePositions = {};

    const svgGroup = d3.select(gRef.current);

    const g = layoutGraph(nodes, links);

    g.nodes().forEach(node => {
      nodePositions[node] = g.node(node);
    });

    const linkEnter = enterLinks(svgGroup, links);

    // Add entering links in the parent’s old position.
    drawLinkLine(linkEnter, nodePositions);

    const nodeEnter = enterNodes(svgGroup, nodes, nodePositions);

    nodeEnter.each((node, i, nodesArray) => {
      // In order to use an arrow function on the .each here we have
      // to access the node via nodesArray rather than using `this`
      const nodeRef = d3.select(nodesArray[i]);
      if (node.id === 1) {
        drawRootNode(nodeRef);
      } else {
        nodeRef
          .append('rect')
          .attr('width', wfConstants.nodeW)
          .attr('height', wfConstants.nodeH)
          .attr('rx', 2)
          .attr('ry', 2)
          .attr('stroke', (d) => {
            if (d.job) {
              if (d.job.status === 'failed' || d.job.status === 'error' || d.job.status === 'canceled') {
                return '#d9534f';
              } else if (d.job.status === 'successful' || d.job.status === 'ok') {
                return '#5cb85c';
              }
            }
            
            return '#93969A';
          })
          .attr('stroke-width', '2px')
          .attr('fill', node.isInvalidLinkTarget ? '#D7D7D7' : '#FFFFFF')
          .attr('class', d => {
            let classString = 'WorkflowGraph-rect';
            classString += !(d.unifiedJobTemplate && d.unifiedJobTemplate.name)
              ? ' WorkflowGraph-dashedNode'
              : '';
            return classString;
          });

        nodeRef
          .append('foreignObject')
          .attr('width', wfConstants.nodeW)
          .attr('height', wfConstants.nodeH)
          .attr('class', 'WorkflowGraph-nodeContents')
          .html(
            d => {
              if (d.job) {
                let elapsed;
                if (d.job.elapsed) {
                  elapsed = `<div class="WorkflowGraph-elapsedWrapper">
                    <span class="WorkflowGraph-elapsedText">${secondsToHHMMSS(d.job.elapsed)}</span>
                  </div>`;
                }
                let jobStatus;
                if (d.job.status === 'running') {
                  jobStatus = `<div class="WorkflowGraph-jobStatus WorkflowGraph-jobStatus--running"></div>`;
                } else if (d.job.status === 'new' ||
                d.job.status === 'pending' ||
                d.job.status === 'waiting' ||
                d.job.status === 'never updated') {
                  jobStatus = `<div class="WorkflowGraph-jobStatus WorkflowGraph-jobStatus--waiting"></div>`;
                } else if (d.job.status === 'failed' || d.job.status === 'error' || d.job.status === 'canceled') {
                  jobStatus = `
                    <div class="WorkflowGraph-jobStatus WorkflowGraph-jobStatus--split">
                      <div class="WorkflowGraph-jobStatus--whiteTop"></div>
                      <div class="WorkflowGraph-jobStatus--fail"></div>
                    </div>
                  `;
                } else if (d.job.status === 'successful' || d.job.status === 'ok') {
                  jobStatus = `
                    <div class="WorkflowGraph-jobStatus WorkflowGraph-jobStatus--split">
                      <div class="WorkflowGraph-jobStatus--success"></div>
                      <div class="WorkflowGraph-jobStatus--whiteBottom"></div>
                    </div>
                  `;
                }
                return `
                  <div class="WorkflowGraph-jobTopLine">
                    ${jobStatus}
                    <p class="WorkflowGraph-ellipsisText">${
                      d.unifiedJobTemplate
                        ? d.unifiedJobTemplate.name
                        : i18n._(t`DELETED`)
                    }</p>
                  </div>
                  ${elapsed}
                `;
              } else {
                return `<p class="WorkflowGraph-nameText WorkflowGraph-ellipsisText">${
                  d.unifiedJobTemplate
                    ? d.unifiedJobTemplate.name
                    : i18n._(t`DELETED`)
                }</p>`;
              }
            }

          );

        nodeRef
          .append('rect')
          .attr('width', wfConstants.nodeW)
          .attr('height', wfConstants.nodeH)
          .attr('class', 'WorkflowGraph-nodeOverlay')
          .style('opacity', '0')
          .on('mouseenter', d => {
            if (d.job) {
              nodeRef.select('.WorkflowGraph-nodeOverlay').style('cursor', 'pointer');
            }
            setHelpText(d);
          })
          .on('mouseleave', () => {
            nodeRef.select('.WorkflowGraph-nodeOverlay').style('cursor', 'default');
            setHelpText(null);
          })
          .on('click', (d) => {
            if (d.job) {
              window.open(`/#/jobs/${JOB_TYPE_URL_SEGMENTS[d.job.type]}/${d.job.id}`,'_blank');
            }
          });

        drawNodeTypeLetter(nodeRef);
      }
    });

    // This will make sure that all the link elements appear before the nodes in the dom
    svgGroup.selectAll('.WorkflowGraph-node').order();
  }, [links, nodes]);

  // Attempt to zoom the graph to fit the available screen space
  useEffect(() => {
    const gBoundingClientRect = d3
      .select(gRef.current)
      .node()
      .getBoundingClientRect();

    const gBBoxDimensions = d3
      .select(gRef.current)
      .node()
      .getBBox();

    // For some reason the root width needs to be added?
    gBoundingClientRect.width += wfConstants.rootW;

    const svgElement = document.getElementById("workflow-svg");
    const svgBoundingClientRect = svgElement.getBoundingClientRect();

    const [scaleToFit, yTranslate] = calcZoomAndFit(svgBoundingClientRect, gBoundingClientRect, gBBoxDimensions);

    d3.select(svgRef.current).call(
      zoomRef.transform,
      d3.zoomIdentity
        .translate(0, yTranslate)
        .scale(scaleToFit)
    );
    // We only want this to run once (when the component mounts)
    // but this rule will throw a warning if we don't include
    // things like height, width, currentScale in the array
    // of deps.  Including them will cause this hook to fire
    // as those deps change.
    // Discussion: https://github.com/facebook/create-react-app/issues/6880
    // and https://github.com/facebook/react/issues/15865 amongst others
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <Fragment>
      {helpText && helpText !== '' && (
        <WorkflowHelp>
          {typeof helpText === 'string' && <Fragment>{helpText}</Fragment>}
          {typeof helpText === 'object' && <WorkflowHelpDetails d={helpText} />}
        </WorkflowHelp>
      )}
      <svg id="workflow-svg" ref={svgRef}>
        <g id="workflow-g" ref={gRef} />
      </svg>
    </Fragment>
  );
}

export default Graph;