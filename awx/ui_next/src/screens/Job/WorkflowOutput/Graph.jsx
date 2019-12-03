import React, { Fragment, useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import * as dagre from 'dagre';
import styled from 'styled-components';
import WorkflowHelp from './WorkflowHelp';
import WorkflowHelpDetails from './WorkflowHelpDetails';

const SVG = styled.svg`
  display: flex;
  height: 100%;
  background-color: #F6F6F6;
`;

function Graph({
  links,
  nodes,
}) {
  const [helpText, setHelpText] = useState();
  const svgRef = useRef(null);
  const gRef = useRef(null);
  const backgroundRef = useRef(null);
  const nodeW = 180;
  const nodeH = 60;
  // This needs to be dynamic bc the text can be different lengths in different languages
  const rootW = 72;
  const rootH = 40;

  // Dagre is going to shift the root node around as nodes are added/removed
  // This function ensures that the user doesn't experience that
  const normalizeY = (nodePositions, y) => {
    return y - nodePositions[1].y;
  };

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
    const line = d3
      .line()
      .x(d => {
        return d.x;
      })
      .y(d => {
        return d.y;
      });
    const lineData = d => {
      const sourceX =
        nodePositions[d.source.id].x + nodePositions[d.source.id].width + 1;
      let sourceY =
        normalizeY(nodePositions, nodePositions[d.source.id].y) +
        nodePositions[d.source.id].height / 2;
      const targetX = nodePositions[d.target.id].x - 1;
      const targetY =
        normalizeY(nodePositions, nodePositions[d.target.id].y) +
        nodePositions[d.target.id].height / 2;

      // There's something off with the math on the root node...
      if (d.source.id === 1) {
        sourceY += 10;
      }

      return line([
        {
          x: sourceX,
          y: sourceY,
        },
        {
          x: targetX,
          y: targetY,
        },
      ]);
    };

    const svgGroup = d3.select(gRef.current);

    const g = new dagre.graphlib.Graph();

    g.setGraph({ rankdir: 'LR', nodesep: 30, ranksep: 120 });

    // This is needed for Dagre
    g.setDefaultEdgeLabel(() => {
      return {};
    });

    nodes.forEach(node => {
      if (node.id === 1) {
        g.setNode(node.id, { label: '', width: rootW, height: rootH });
      } else {
        g.setNode(node.id, { label: '', width: nodeW, height: nodeH });
      }
    });

    links.forEach(link => {
      g.setEdge(link.source.id, link.target.id);
    });

    dagre.layout(g);

    g.nodes().forEach(node => {
      nodePositions[node] = g.node(node);
    });

    const linkRefs = svgGroup
      .selectAll('.WorkflowChart-link')
      .data(links, d => {
        return `${d.source.id}-${d.target.id}`;
      });

    // Add any new links
    const linkEnter = linkRefs
      .enter()
      .append('g')
      .attr('class', 'WorkflowChart-link')
      .attr('id', d => `link-${d.source.id}-${d.target.id}`)
      .attr('stroke-width', '2px');

    // Add entering links in the parent’s old position.
    linkEnter
      .insert('path', 'g')
      .attr('class', 'WorkflowChart-linkPath')
      .attr('d', d => lineData(d))
      .attr('stroke', d => {
        if (d.edgeType) {
          if (d.edgeType === 'failure') {
            return '#d9534f';
          }
          if (d.edgeType === 'success') {
            return '#5cb85c';
          }
          if (d.edgeType === 'always') {
            return '#337ab7';
          }
        }
        return '#D7D7D7';
      });

    const nodeRefs = svgGroup
      .selectAll('.WorkflowChart-node')
      .data(nodes, d => {
        return d.id;
      });

    // Add new nodes
    const nodeEnter = nodeRefs
      .enter()
      .append('g')
      .attr('class', 'WorkflowChart-node')
      .attr('id', d => `node-${d.id}`)
      .attr(
        'transform',
        d =>
          `translate(${nodePositions[d.id].x},${normalizeY(
            nodePositions,
            nodePositions[d.id].y
          )})`
      );

    nodeEnter.each((node, i, nodesArray) => {
      // In order to use an arrow function on the .each here we have
      // to access the node via nodesArray rather than using `this`
      const nodeRef = d3.select(nodesArray[i]);
      if (node.id === 1) {
        nodeRef
          .append('rect')
          .attr('width', rootW)
          .attr('height', rootH)
          .attr('y', 10)
          .attr('rx', 2)
          .attr('ry', 2)
          .attr('fill', '#0279BC')
          .attr('class', 'WorkflowChart-rootNode');
        nodeRef
          .append('text')
          .attr('x', 13)
          .attr('y', 30)
          .attr('dy', '.35em')
          .attr('fill', 'white')
          .attr('class', 'WorkflowChart-startText')
          .text('START');
      } else {
        nodeRef
          .append('rect')
          .attr('width', nodeW)
          .attr('height', nodeH)
          .attr('rx', 2)
          .attr('ry', 2)
          .attr('stroke', '#93969A')
          .attr('stroke-width', '2px')
          .attr('fill', node.isInvalidLinkTarget ? '#D7D7D7' : '#FFFFFF')
          .attr('class', d => {
            let classString = 'WorkflowChart-rect';
            classString += !(d.unifiedJobTemplate && d.unifiedJobTemplate.name)
              ? ' WorkflowChart-dashedNode'
              : '';
            return classString;
          });

        nodeRef
          .append('text')
          .attr('x', () => {
            return nodeW / 2;
          })
          .attr('y', () => {
            return nodeH / 2;
          })
          .attr('dy', '.35em')
          .attr('text-anchor', 'middle')
          .attr('class', 'WorkflowChart-defaultText WorkflowChart-nameText')
          .text(d =>
            d.unifiedJobTemplate && d.unifiedJobTemplate.name
              ? d.unifiedJobTemplate.name
              : 'NO NAME'
          );

        nodeRef
          .append('rect')
          .attr('width', nodeW)
          .attr('height', nodeH)
          .attr('class', 'WorkflowChart-nodeOverlay')
          .style('opacity', '0')
          .on('mouseenter', d => {
            setHelpText(d);
          })
          .on('mouseleave', () => {
            setHelpText(null);
          });

        nodeRef
          .append('circle')
          .attr('cy', nodeH)
          .attr('r', 10)
          .attr('class', 'WorkflowChart-nodeTypeCircle')
          .attr('fill', '#393F43')
          .style('display', d => (d.unifiedJobTemplate ? null : 'none'));

        nodeRef
          .append('text')
          .attr('y', nodeH)
          .attr('dy', '.35em')
          .attr('text-anchor', 'middle')
          .attr('fill', '#FFFFFF')
          .attr('class', 'WorkflowChart-nodeTypeLetter')
          .text(d => {
            let nodeTypeLetter;
            if (d.unifiedJobTemplate && d.unifiedJobTemplate.type) {
              switch (d.unifiedJobTemplate.type) {
                case 'job_template':
                  nodeTypeLetter = 'JT';
                  break;
                case 'project':
                  nodeTypeLetter = 'P';
                  break;
                case 'inventory_source':
                  nodeTypeLetter = 'I';
                  break;
                case 'workflow_job_template':
                  nodeTypeLetter = 'W';
                  break;
                default:
                  nodeTypeLetter = '';
              }
            } else if (
              d.unifiedJobTemplate &&
              d.unifiedJobTemplate.unified_job_type
            ) {
              switch (d.unifiedJobTemplate.unified_job_type) {
                case 'job':
                  nodeTypeLetter = 'JT';
                  break;
                case 'project_update':
                  nodeTypeLetter = 'P';
                  break;
                case 'inventory_update':
                  nodeTypeLetter = 'I';
                  break;
                case 'workflow_job':
                  nodeTypeLetter = 'W';
                  break;
                default:
                  nodeTypeLetter = '';
              }
            }
            return nodeTypeLetter;
          })
          .style('font-size', '10px')
          .style('display', d => {
            return d.unifiedJobTemplate &&
              d.unifiedJobTemplate.type !== 'workflow_approval_template' &&
              d.unifiedJobTemplate.unified_job_type !== 'workflow_approval'
              ? null
              : 'none';
          });
      }
    });

    // This will make sure that all the link elements appear before the nodes in the dom
    svgGroup.selectAll('.WorkflowChart-node').order();
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
    gBoundingClientRect.width += rootW;

    const svgElement = document.getElementById("workflow-svg");
    const svgBoundingClientRect = svgElement.getBoundingClientRect();

    const scaleNeededForMaxHeight =
      svgBoundingClientRect.height / gBoundingClientRect.height;
    const scaleNeededForMaxWidth =
      svgBoundingClientRect.width / gBoundingClientRect.width;
    const lowerScale = Math.min(
      scaleNeededForMaxHeight,
      scaleNeededForMaxWidth
    );

    let scaleToFit;
    let yTranslate;
    if (lowerScale < 0.1 || lowerScale > 2) {
      scaleToFit = lowerScale < 0.1 ? 0.1 : 2;
      yTranslate = svgBoundingClientRect.height / 2 - (nodeH * scaleToFit) / 2;
    } else {
      scaleToFit = Math.floor(lowerScale * 1000) / 1000;
      yTranslate = (svgBoundingClientRect.height - gBoundingClientRect.height*scaleToFit)/2 - gBBoxDimensions.y*scaleToFit;
    }

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
      <SVG id="workflow-svg" ref={svgRef}>
        <rect
          width="100%"
          height="100%"
          opacity="0"
          id="workflow-backround"
          ref={backgroundRef}
        />
        <g id="workflow-g" ref={gRef} />
      </SVG>
    </Fragment>
  );
}

export default Graph;