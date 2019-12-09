/* eslint-disable import/prefer-default-export */
import * as d3 from 'd3';
import * as dagre from 'dagre';

export const constants = {
  nodeW: 180,
  nodeH: 60,
  rootW: 72,
  rootH: 40,
};

export function calcZoomAndFit(svgBounds, gBounds, gBBoxDimensions) {
  const scaleNeededForMaxHeight = svgBounds.height / gBounds.height;
  const scaleNeededForMaxWidth = svgBounds.width / gBounds.width;
  const lowerScale = Math.min(scaleNeededForMaxHeight, scaleNeededForMaxWidth);

  let scaleToFit;
  let yTranslate;
  if (lowerScale < 0.1 || lowerScale > 2) {
    scaleToFit = lowerScale < 0.1 ? 0.1 : 2;
    yTranslate = svgBounds.height / 2 - (constants.nodeH * scaleToFit) / 2;
  } else {
    scaleToFit = Math.floor(lowerScale * 1000) / 1000;
    yTranslate =
      (svgBounds.height - gBounds.height * scaleToFit) / 2 -
      gBBoxDimensions.y * scaleToFit;
  }

  return [scaleToFit, yTranslate];
}

export function normalizeY(nodePositions, y) {
  return y - nodePositions[1].y;
}

export function lineData(link, nodePositions) {
  const line = d3
    .line()
    .x(d => {
      return d.x;
    })
    .y(d => {
      return d.y;
    });

  const sourceX =
    nodePositions[link.source.id].x + nodePositions[link.source.id].width + 1;
  let sourceY =
    normalizeY(nodePositions, nodePositions[link.source.id].y) +
    nodePositions[link.source.id].height / 2;
  const targetX = nodePositions[link.target.id].x - 1;
  const targetY =
    normalizeY(nodePositions, nodePositions[link.target.id].y) +
    nodePositions[link.target.id].height / 2;

  // There's something off with the math on the root node...
  if (link.source.id === 1) {
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
}

export function getLinkOverlayPoints(d, nodePositions) {
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
  const slope = (targetY - sourceY) / (targetX - sourceX);
  const yIntercept = targetY - slope * targetX;
  const orthogonalDistance = 8;

  const pt1 = [
    targetX,
    slope * targetX +
      yIntercept +
      orthogonalDistance * Math.sqrt(1 + slope * slope),
  ].join(',');
  const pt2 = [
    sourceX,
    slope * sourceX +
      yIntercept +
      orthogonalDistance * Math.sqrt(1 + slope * slope),
  ].join(',');
  const pt3 = [
    sourceX,
    slope * sourceX +
      yIntercept -
      orthogonalDistance * Math.sqrt(1 + slope * slope),
  ].join(',');
  const pt4 = [
    targetX,
    slope * targetX +
      yIntercept -
      orthogonalDistance * Math.sqrt(1 + slope * slope),
  ].join(',');

  return [pt1, pt2, pt3, pt4].join(' ');
}

export function layoutGraph(nodes, links) {
  const g = new dagre.graphlib.Graph();
  g.setGraph({ rankdir: 'LR', nodesep: 30, ranksep: 120 });

  // This is needed for Dagre
  g.setDefaultEdgeLabel(() => {
    return {};
  });

  nodes.forEach(node => {
    if (node.id === 1) {
      g.setNode(node.id, {
        label: '',
        width: constants.rootW,
        height: constants.rootH,
      });
    } else {
      g.setNode(node.id, {
        label: '',
        width: constants.nodeW,
        height: constants.nodeH,
      });
    }
  });

  links.forEach(link => {
    g.setEdge(link.source.id, link.target.id);
  });

  dagre.layout(g);

  return g;
}

export function drawRootNode(nodeRef) {
  nodeRef
    .append('rect')
    .attr('width', constants.rootW)
    .attr('height', constants.rootH)
    .attr('y', 10)
    .attr('rx', 2)
    .attr('ry', 2)
    .attr('fill', '#0279BC')
    .attr('class', 'WorkflowGraph-rootNode');
  nodeRef
    .append('text')
    .attr('x', 13)
    .attr('y', 30)
    .attr('dy', '.35em')
    .attr('fill', 'white')
    .attr('class', 'WorkflowGraph-startText')
    .text('START');
}

export function drawLinkLine(linkEnter, nodePositions) {
  linkEnter
    .insert('path', 'g')
    .attr('class', 'WorkflowGraph-linkPath')
    .attr('d', d => lineData(d, nodePositions))
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
}

export function drawNodeTypeLetter(nodeRef) {
  nodeRef
    .append('circle')
    .attr('cy', constants.nodeH)
    .attr('r', 10)
    .attr('class', 'WorkflowGraph-nodeTypeCircle')
    .attr('fill', '#393F43')
    .style('display', d => (d.unifiedJobTemplate ? null : 'none'));
  nodeRef
    .append('text')
    .attr('y', constants.nodeH)
    .attr('dy', '.35em')
    .attr('text-anchor', 'middle')
    .attr('fill', '#FFFFFF')
    .attr('class', 'WorkflowGraph-nodeTypeLetter')
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

export function enterLinks(svgGroup, links) {
  const linkRefs = svgGroup.selectAll('.WorkflowGraph-link').data(links, d => {
    return `${d.source.id}-${d.target.id}`;
  });

  // Remove any stale links
  linkRefs.exit().remove();

  return linkRefs
    .enter()
    .append('g')
    .attr('class', 'WorkflowGraph-link')
    .attr('id', d => `link-${d.source.id}-${d.target.id}`)
    .attr('stroke-width', '2px');
}

export function enterNodes(svgGroup, nodes, nodePositions) {
  const nodeRefs = svgGroup.selectAll('.WorkflowGraph-node').data(nodes, d => {
    return d.id;
  });

  // Remove any stale nodes
  nodeRefs.exit().remove();

  return nodeRefs
    .enter()
    .append('g')
    .attr('class', 'WorkflowGraph-node')
    .attr('id', d => `node-${d.id}`)
    .attr(
      'transform',
      d =>
        `translate(${nodePositions[d.id].x},${normalizeY(
          nodePositions,
          nodePositions[d.id].y
        )})`
    );
}
