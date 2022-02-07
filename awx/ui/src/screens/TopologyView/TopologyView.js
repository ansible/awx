import React, { useEffect, useCallback, useState } from 'react';
import * as d3 from 'd3';
import { t } from '@lingui/macro';
import { PageSection, Card, CardBody } from '@patternfly/react-core';
import useRequest from 'hooks/useRequest';
import { MeshAPI } from 'api';
import Header from './Header';
import MeshGraph from './MeshGraph';

function TopologyView() {
  const [showLegend, setShowLegend] = useState(true);
  const {
    isLoading,
    result: { meshData },
    // error: fetchInitialError,
    request: fetchMeshVisualizer,
  } = useRequest(
    useCallback(async () => {
      const { data } = await MeshAPI.read();
      return {
        meshData: data,
      };
    }, []),
    { meshData: { nodes: [], links: [] } }
  );
  useEffect(() => {
    fetchMeshVisualizer();
  }, [fetchMeshVisualizer]);

  const zoom = d3.zoom().on('zoom', ({ transform }) => {
    d3.select('.mesh').attr('transform', transform);
  });
  const zoomIn = () => {
    d3.select('.mesh-svg').transition().call(zoom.scaleBy, 2);
  };
  const zoomOut = () => {
    d3.select('.mesh-svg').transition().call(zoom.scaleBy, 0.5);
  };
  const resetZoom = () => {
    const margin = 15;
    const height = 600;
    const width = parseInt(d3.select(`#chart`).style('width'), 10) - margin;
    d3.select('.mesh-svg')
      .transition()
      .duration(750)
      .call(
        zoom.transform,
        d3.zoomIdentity,
        d3
          .zoomTransform(d3.select('.mesh-svg').node())
          .invert([width / 2, height / 2])
      );
  };

  const zoomFit = () => {
    const bounds = d3.select('.mesh').node().getBBox();
    const parent = d3.select('.mesh').node().parentElement;
    const fullWidth = parent.clientWidth;
    const fullHeight = parent.clientHeight;
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
    d3.select('.mesh-svg')
      .transition()
      .duration(750)
      .call(zoom.transform, d3.zoomIdentity.translate(x, y).scale(scale));
  };

  return (
    <>
      <Header
        title={t`Topology View`}
        handleSwitchToggle={setShowLegend}
        toggleState={showLegend}
        zoomIn={zoomIn}
        zoomOut={zoomOut}
        zoomFit={zoomFit}
        resetZoom={resetZoom}
      />
      <PageSection>
        <Card>
          <CardBody>
            {!isLoading && (
              <MeshGraph data={meshData} showLegend={showLegend} zoom={zoom} />
            )}
          </CardBody>
        </Card>
      </PageSection>
    </>
  );
}

export default TopologyView;
