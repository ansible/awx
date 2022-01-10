import React, { useCallback, useEffect } from 'react';

import { t } from '@lingui/macro';
import { Host } from 'types';
import { CardBody } from 'components/Card';
import { DetailList } from 'components/DetailList';
import { VariablesDetail } from 'components/CodeEditor';
import ContentError from 'components/ContentError';
import ContentLoading from 'components/ContentLoading';
import useRequest from 'hooks/useRequest';
import { HostsAPI } from 'api';

function HostFacts({ host }) {
  const {
    result: facts,
    isLoading,
    error,
    request: fetchFacts,
  } = useRequest(
    useCallback(async () => {
      const [{ data: factsObj }] = await Promise.all([
        HostsAPI.readFacts(host.id),
      ]);
      return JSON.stringify(factsObj, null, 4);
    }, [host]),
    '{}'
  );

  useEffect(() => {
    fetchFacts();
  }, [fetchFacts]);

  if (isLoading) {
    return <ContentLoading />;
  }

  if (error) {
    return <ContentError error={error} />;
  }

  return (
    <CardBody>
      <DetailList gutter="sm">
        <VariablesDetail
          label={t`Facts`}
          rows="auto"
          value={facts}
          name="facts"
          dataCy="host-facts-detail"
        />
      </DetailList>
    </CardBody>
  );
}

HostFacts.propTypes = {
  host: Host.isRequired,
};

export default HostFacts;
