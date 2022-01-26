import React, { useEffect, useCallback } from 'react';
import { useHistory } from 'react-router-dom';

import { t } from '@lingui/macro';
import ScreenHeader from 'components/ScreenHeader/ScreenHeader';
import { PageSection, Card, CardBody } from '@patternfly/react-core';
import useRequest from 'hooks/useRequest';
import { MeshAPI, InstancesAPI } from 'api';
import MeshGraph from './MeshGraph';

function TopologyView() {
  const {
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
  async function RedirectToDetailsPage({ id: nodeId }) {
    const history = useHistory();
    const {
      data: { results },
    } = await InstancesAPI.readInstanceGroup(nodeId);
    const { id: instanceGroupId } = results[0];
    const constructedURL = `/instance_groups/${instanceGroupId}/instances/${nodeId}/details`;
    history.push(constructedURL);
  }
  useEffect(() => {
    fetchMeshVisualizer();
  }, [fetchMeshVisualizer]);
  return (
    <>
      <ScreenHeader breadcrumbConfig={{ '/topology_view': t`Topology View` }} />

      <PageSection>
        <Card>
          <CardBody>
            {meshData && (
              <MeshGraph
                data={meshData}
                redirectToDetailsPage={RedirectToDetailsPage}
              />
            )}
          </CardBody>
        </Card>
      </PageSection>
    </>
  );
}

export default TopologyView;
