import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { CardBody } from '@patternfly/react-core';
import { DetailList, Detail, UserDateDetail } from '@components/DetailList';
import { ChipGroup, Chip } from '@components/Chip';
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

  const { organization } = inventory.summary_fields;

  return (
    <CardBody>
      <DetailList>
        <Detail label={i18n._(t`Name`)} value={inventory.name} />
        <Detail label={i18n._(t`Activity`)} value="Coming soon" />
        <Detail label={i18n._(t`Description`)} value={inventory.description} />
        <Detail label={i18n._(t`Type`)} value={i18n._(t`Inventory`)} />
        <Detail
          label={i18n._(t`Organization`)}
          value={
            <Link to={`/organizations/${organization.id}/details`}>
              {organization.name}
            </Link>
          }
        />
        <Detail
          fullWidth
          label={i18n._(t`Instance Groups`)}
          value={
            isLoading ? (
              'loading...'
            ) : (
              <ChipGroup numChips={5}>
                {instanceGroups.map(ig => (
                  <Chip key={ig.id} isReadOnly>
                    {ig.name}
                  </Chip>
                ))}
              </ChipGroup>
            )
          }
        />
      </DetailList>
      {inventory.variables && (
        <VariablesDetail
          id="job-artifacts"
          label={i18n._(t`Variables`)}
          value={inventory.variables}
          rows={4}
        />
      )}
      <DetailList>
        <UserDateDetail
          label={i18n._(t`Created`)}
          date={inventory.created}
          user={inventory.summary_fields.created_by}
        />
        <UserDateDetail
          label={i18n._(t`Last Modified`)}
          date={inventory.modified}
          user={inventory.summary_fields.modified_by}
        />
      </DetailList>
    </CardBody>
  );
}
InventoryDetail.propTypes = {
  inventory: Inventory.isRequired,
};

export default withI18n()(InventoryDetail);
