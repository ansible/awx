import React, { useState, useEffect } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { CardBody } from '@components/Card';
import { DetailList, Detail } from '@components/DetailList';
import { VariablesDetail } from '@components/CodeMirrorInput';
import { InventoriesAPI } from '@api';
import { Inventory } from '../../../types';

function InventoryDetail({ inventory, i18n }) {
  const [instanceGroups, setInstanceGroups] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    (async () => {
      setIsLoading(true);
      const { data } = await InventoriesAPI.readInstanceGroups(inventory.id);
      setInstanceGroups(data.results);
      setIsLoading(false);
    })();
  }, [inventory.id]);

  return (
    <CardBody>
      <DetailList>
        <Detail label={i18n._(t`Name`)} value={inventory.name} />
        <Detail label={i18n._(t`Activity`)} value="Coming soon" />
        <Detail label={i18n._(t`Description`)} value={inventory.description} />
        <Detail label={i18n._(t`Type`)} value={inventory.kind} />
        <Detail
          label={i18n._(t`Organization`)}
          value={inventory.summary_fields.organization.name}
        />
        <Detail
          fullWidth
          label={i18n._(t`Instance Groups`)}
          value={isLoading ? 'loading...' : instanceGroups.map(g => g.name)}
        />
      </DetailList>
      {inventory.variables && (
        <VariablesDetail
          id="job-artifacts"
          value={inventory.variables}
          rows={4}
          label={i18n._(t`Variables`)}
        />
      )}{' '}
      <Detail label={i18n._(t`Description`)} value={inventory.description} />
    </CardBody>
  );
}
InventoryDetail.propTypes = {
  inventory: Inventory.isRequired,
};

export default withI18n()(InventoryDetail);
