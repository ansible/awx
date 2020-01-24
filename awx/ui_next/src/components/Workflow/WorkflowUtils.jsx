/* eslint-disable import/prefer-default-export */
import * as d3 from 'd3';
import * as dagre from 'dagre';

const normalizeY = (nodePositions, y) => y - nodePositions[1].y;

export const constants = {
  nodeW: 180,
  nodeH: 60,
  rootW: 72,
  rootH: 40,
};

export function getScaleAndOffsetToFit(
  gBoundingClientRect,
  svgBoundingClientRect,
  gBBoxDimensions,
  currentScale
) {
  gBoundingClientRect.height /= currentScale;
  gBoundingClientRect.width /= currentScale;

  // For some reason the root width needs to be added?
  gBoundingClientRect.width += constants.rootW;

  const scaleNeededForMaxHeight =
    svgBoundingClientRect.height / gBoundingClientRect.height;
  const scaleNeededForMaxWidth =
    svgBoundingClientRect.width / gBoundingClientRect.width;
  const lowerScale = Math.min(scaleNeededForMaxHeight, scaleNeededForMaxWidth);

  let scaleToFit;
  let yTranslate;
  if (lowerScale < 0.1 || lowerScale > 2) {
    scaleToFit = lowerScale < 0.1 ? 0.1 : 2;
    yTranslate =
      svgBoundingClientRect.height / 2 - (constants.nodeH * scaleToFit) / 2;
  } else {
    scaleToFit = Math.floor(lowerScale * 1000) / 1000;
    yTranslate =
      (svgBoundingClientRect.height - gBoundingClientRect.height * scaleToFit) /
        2 -
      (gBBoxDimensions.y / currentScale) * scaleToFit;
  }

  return [scaleToFit, yTranslate];
}

export function generateLine(points) {
  const line = d3
    .line()
    .x(d => {
      return d.x;
    })
    .y(d => {
      return d.y;
    });

  return line(points);
}

export function getLinePoints(link, nodePositions) {
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

  return [
    {
      x: sourceX,
      y: sourceY,
    },
    {
      x: targetX,
      y: targetY,
    },
  ];
}

export function getLinkOverlayPoints(link, nodePositions) {
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

export function getTranslatePointsForZoom(
  svgBoundingClientRect,
  currentScaleAndOffset,
  newScale
) {
  const origScale = currentScaleAndOffset.k;
  const unscaledOffsetX =
    (currentScaleAndOffset.x +
      (svgBoundingClientRect.width * origScale - svgBoundingClientRect.width) /
        2) /
    origScale;
  const unscaledOffsetY =
    (currentScaleAndOffset.y +
      (svgBoundingClientRect.height * origScale -
        svgBoundingClientRect.height) /
        2) /
    origScale;
  const translateX =
    unscaledOffsetX * newScale -
    (newScale * svgBoundingClientRect.width - svgBoundingClientRect.width) / 2;
  const translateY =
    unscaledOffsetY * newScale -
    (newScale * svgBoundingClientRect.height - svgBoundingClientRect.height) /
      2;
  return [translateX, translateY];
}
