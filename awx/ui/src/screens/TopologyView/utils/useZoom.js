import * as d3 from 'd3';
import { getWidth, getHeight } from './helpers';

/**
 * useZoom provides a collection of zoom behaviors/functions for D3 graphs
 * Params: string value of parent and child classnames
 * The following hierarchy should be followed:
 * <div id="chart">
 *  <svg><-- parent -->
 *    <g><-- child -->
 *  </svg>
 * </div>
 * Returns: {
 *  zoom: d3 zoom behavior/object/function to apply on selected elements
 *  zoomIn: function that zooms in
 *  zoomOut: function that zooms out
 *  zoomFit: function that scales child element to fit within parent element
 *  resetZoom: function resets the zoom level to its initial value
 * }
 */

export default function useZoom(parentSelector, childSelector) {
  const zoom = d3.zoom().on('zoom', ({ transform }) => {
    d3.select(childSelector).attr('transform', transform);
  });
  const zoomIn = () => {
    d3.select(parentSelector).transition().call(zoom.scaleBy, 2);
  };
  const zoomOut = () => {
    d3.select(parentSelector).transition().call(zoom.scaleBy, 0.5);
  };
  const resetZoom = () => {
    const parent = d3.select(parentSelector).node();
    const width = parent.clientWidth;
    const height = parent.clientHeight;
    d3.select(parentSelector)
      .transition()
      .duration(750)
      .call(
        zoom.transform,
        d3.zoomIdentity,
        d3
          .zoomTransform(d3.select(parentSelector).node())
          .invert([width / 2, height / 2])
      );
  };
  const zoomFit = () => {
    const bounds = d3.select(childSelector).node().getBBox();
    const fullWidth = getWidth(parentSelector);
    const fullHeight = getHeight(parentSelector);
    const { width, height } = bounds;
    const midX = bounds.x + width / 2;
    const midY = bounds.y + height / 2;
    if (width === 0 || height === 0) return; // nothing to fit
    const scale = 0.8 / Math.max(width / fullWidth, height / fullHeight);
    const translate = [
      fullWidth / 2 - scale * midX,
      fullHeight / 2 - scale * midY,
    ];
    const [x, y] = translate;
    d3.select(parentSelector)
      .transition()
      .duration(750)
      .call(zoom.transform, d3.zoomIdentity.translate(x, y).scale(scale));
  };

  return {
    zoom,
    zoomIn,
    zoomOut,
    zoomFit,
    resetZoom,
  };
}
