import React, { useEffect, useCallback, useState } from 'react';
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
  return (
    <>
      <Header
        title={t`Topology View`}
        handleSwitchToggle={setShowLegend}
        toggleState={showLegend}
      />
      <PageSection>
        <Card>
          <CardBody>
            {!isLoading && (
              <MeshGraph data={meshData} showLegend={showLegend} />
            )}
          </CardBody>
        </Card>
      </PageSection>
    </>
  );
}

export default TopologyView;
