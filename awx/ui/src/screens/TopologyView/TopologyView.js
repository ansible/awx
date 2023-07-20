import React, { useEffect, useCallback, useState, useRef } from 'react';
import { t } from '@lingui/macro';
import { PageSection, Card, CardBody } from '@patternfly/react-core';
import ContentError from 'components/ContentError';
import useRequest from 'hooks/useRequest';
import { MeshAPI } from 'api';
import Header from './Header';
import MeshGraph from './MeshGraph';
import useZoom from './utils/useZoom';
import { CHILDSELECTOR, PARENTSELECTOR } from './constants';

function TopologyView() {
  const storedNodes = useRef(null);
  const [showLegend, setShowLegend] = useState(true);
  const [showZoomControls, setShowZoomControls] = useState(false);
  const {
    isLoading,
    result: { meshData },
    error: fetchInitialError,
    request: fetchMeshVisualizer,
  } = useRequest(
    useCallback(async () => {
      const { data } = await MeshAPI.read();
      storedNodes.current = data.nodes;
      return {
        meshData: data,
      };
    }, []),
    { meshData: { nodes: [], links: [] } }
  );
  useEffect(() => {
    fetchMeshVisualizer();
  }, [fetchMeshVisualizer]);
  const { zoom, zoomFit, zoomIn, zoomOut, resetZoom } = useZoom(
    PARENTSELECTOR,
    CHILDSELECTOR
  );

  return (
    <>
      <Header
        title={t`Topology View`}
        handleSwitchToggle={setShowLegend}
        toggleState={showLegend}
        zoomIn={zoomIn}
        zoomOut={zoomOut}
        zoomFit={zoomFit}
        refresh={fetchMeshVisualizer}
        resetZoom={resetZoom}
        showZoomControls={showZoomControls}
      />
      {fetchInitialError ? (
        <PageSection>
          <Card>
            <CardBody>
              <ContentError error={fetchInitialError} />
            </CardBody>
          </Card>
        </PageSection>
      ) : (
        <PageSection>
          <Card style={{ height: '100%' }}>
            <CardBody>
              {!isLoading && (
                <MeshGraph
                  data={meshData}
                  showLegend={showLegend}
                  zoom={zoom}
                  setShowZoomControls={setShowZoomControls}
                  storedNodes={storedNodes}
                />
              )}
            </CardBody>
          </Card>
        </PageSection>
      )}
    </>
  );
}

export default TopologyView;
