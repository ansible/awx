import {
  getScaleAndOffsetToFit,
  generateLine,
  getLinePoints,
  getLinkOverlayPoints,
  layoutGraph,
  getTranslatePointsForZoom,
} from './WorkflowUtils';

describe('getScaleAndOffsetToFit', () => {
  const gBoundingClientRect = {
    x: 36,
    y: 11,
    width: 798,
    height: 160,
    top: 11,
    right: 834,
    bottom: 171,
    left: 36,
  };
  const svgBoundingClientRect = {
    x: 0,
    y: 56,
    width: 1680,
    height: 455,
    top: 56,
    right: 1680,
    bottom: 511,
    left: 0,
  };
  const gBBoxDimensions = {
    x: 36,
    y: -45,
    width: 726,
    height: 160,
  };
  const currentScale = 1;
  test('returns correct scale and y-offset for zooming the graph to best fit the available space', () => {
    expect(
      getScaleAndOffsetToFit(
        gBoundingClientRect,
        svgBoundingClientRect,
        gBBoxDimensions,
        currentScale
      )
    ).toEqual([1.931, 159.91499999999996]);
  });
});

describe('generateLine', () => {
  test('returns correct svg path string', () => {
    expect(
      generateLine([
        {
          x: 0,
          y: 0,
        },
        {
          x: 10,
          y: 10,
        },
      ])
    ).toEqual('M0,0L10,10');
    expect(
      generateLine([
        {
          x: 900,
          y: 44,
        },
        {
          x: 5000,
          y: 359,
        },
      ])
    ).toEqual('M900,44L5000,359');
  });
});

describe('getLinePoints', () => {
  const link = {
    source: {
      id: 1,
    },
    target: {
      id: 2,
    },
  };
  const nodePositions = {
    1: {
      width: 72,
      height: 40,
      x: 36,
      y: 130,
    },
    2: {
      width: 180,
      height: 60,
      x: 282,
      y: 40,
    },
  };
  test('returns the correct endpoints of the line', () => {
    expect(getLinePoints(link, nodePositions)).toEqual([
      { x: 109, y: 30 },
      { x: 281, y: -60 },
    ]);
  });
});

describe('getLinkOverlayPoints', () => {
  const link = {
    source: {
      id: 1,
    },
    target: {
      id: 2,
    },
  };
  const nodePositions = {
    1: {
      width: 72,
      height: 40,
      x: 36,
      y: 130,
    },
    2: {
      width: 180,
      height: 60,
      x: 282,
      y: 40,
    },
  };
  test('returns the four points of the polygon that will act as the overlay for the link', () => {
    expect(getLinkOverlayPoints(link, nodePositions)).toEqual(
      '281,-50.970992003685446 109,39.02900799631457 109,20.97099200368546 281,-69.02900799631456'
    );
  });
});

describe('layoutGraph', () => {
  const nodes = [
    {
      id: 1,
    },
    {
      id: 2,
    },
    {
      id: 3,
    },
    {
      id: 4,
    },
  ];
  const links = [
    {
      source: {
        id: 1,
      },
      target: {
        id: 2,
      },
    },
    {
      source: {
        id: 1,
      },
      target: {
        id: 4,
      },
    },
    {
      source: {
        id: 2,
      },
      target: {
        id: 3,
      },
    },
    {
      source: {
        id: 4,
      },
      target: {
        id: 3,
      },
    },
  ];
  test('returns the correct dimensions and positions for the nodes', () => {
    expect(layoutGraph(nodes, links)._nodes).toEqual({
      1: { height: 40, label: '', width: 72, x: 36, y: 75 },
      2: { height: 60, label: '', width: 180, x: 282, y: 30 },
      3: { height: 60, label: '', width: 180, x: 582, y: 75 },
      4: { height: 60, label: '', width: 180, x: 282, y: 120 },
    });
  });
});

describe('getTranslatePointsForZoom', () => {
  const svgBoundingClientRect = {
    x: 0,
    y: 56,
    width: 1680,
    height: 455,
    top: 56,
    right: 1680,
    bottom: 511,
    left: 0,
  };
  const currentScaleAndOffset = {
    k: 2,
    x: 0,
    y: 167.5,
  };
  const newScale = 1.9;
  test('returns the correct translation point', () => {
    expect(
      getTranslatePointsForZoom(
        svgBoundingClientRect,
        currentScaleAndOffset,
        newScale
      )
    ).toEqual([42, 170.5]);
  });
});
