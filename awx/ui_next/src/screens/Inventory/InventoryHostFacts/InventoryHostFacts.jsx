import React, { useCallback, useEffect } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Host } from '../../../types';
import { CardBody } from '../../../components/Card';
import { DetailList } from '../../../components/DetailList';
import { VariablesDetail } from '../../../components/CodeMirrorInput';
import ContentError from '../../../components/ContentError';
import ContentLoading from '../../../components/ContentLoading';
import useRequest from '../../../util/useRequest';
import { HostsAPI } from '../../../api';

function InventoryHostFacts({ i18n, host }) {
  const { request, isLoading, error, result } = useRequest(
    useCallback(async () => {
      const { data } = await HostsAPI.readFacts(host.id);

      return JSON.stringify(data, null, 4);
    }, [host]),
    null
  );

  useEffect(() => {
    request();
  }, [request]);

  if (error) {
    return <ContentError error={error} />;
  }

  if (isLoading || result === null) {
    return <ContentLoading />;
  }

  return (
    <CardBody>
      <DetailList gutter="sm">
        <VariablesDetail label={i18n._(t`Facts`)} fullHeight value={result} />
      </DetailList>
    </CardBody>
  );
}

InventoryHostFacts.propTypes = {
  host: Host.isRequired,
};

export default withI18n()(InventoryHostFacts);
