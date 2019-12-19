import React, { useState, useEffect } from 'react';
import { Link, useHistory } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Button } from '@patternfly/react-core';
import { CardBody, CardActionsRow } from '@components/Card';
import { DetailList, Detail, UserDateDetail } from '@components/DetailList';
import { ChipGroup, Chip } from '@components/Chip';
import { VariablesDetail } from '@components/CodeMirrorInput';
import DeleteButton from '@components/DeleteButton';
import ContentError from '@components/ContentError';
import ContentLoading from '@components/ContentLoading';
import { InventoriesAPI } from '@api';
import { Inventory } from '../../../types';

function InventoryDetail({ inventory, i18n }) {
  const [instanceGroups, setInstanceGroups] = useState([]);
  const [hasContentLoading, setHasContentLoading] = useState(true);
  const [contentError, setContentError] = useState(null);
  const history = useHistory();

  useEffect(() => {
    (async () => {
      setHasContentLoading(true);
      try {
        const { data } = await InventoriesAPI.readInstanceGroups(inventory.id);
        setInstanceGroups(data.results);
      } catch (err) {
        setContentError(err);
      } finally {
        setHasContentLoading(false);
      }
    })();
  }, [inventory.id]);

  const deleteInventory = async () => {
    await InventoriesAPI.destroy(inventory.id);
    history.push(`/inventories`);
  };

  const {
    organization,
    user_capabilities: userCapabilities,
  } = inventory.summary_fields;

  if (hasContentLoading) {
    return <ContentLoading />;
  }

  if (contentError) {
    return <ContentError error={contentError} />;
  }

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
            <ChipGroup numChips={5}>
              {instanceGroups.map(ig => (
                <Chip key={ig.id} isReadOnly>
                  {ig.name}
                </Chip>
              ))}
            </ChipGroup>
          }
        />
        <VariablesDetail
          label={i18n._(t`Variables`)}
          value={inventory.variables}
          rows={4}
        />
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
      <CardActionsRow>
        {userCapabilities.edit && (
          <Button
            component={Link}
            to={`/inventories/inventory/${inventory.id}/edit`}
          >
            {i18n._(t`Edit`)}
          </Button>
        )}
        {userCapabilities.delete && (
          <DeleteButton
            name={inventory.name}
            modalTitle={i18n._(t`Delete Inventory`)}
            onConfirm={deleteInventory}
          >
            {i18n._(t`Delete`)}
          </DeleteButton>
        )}
      </CardActionsRow>
    </CardBody>
  );
}
InventoryDetail.propTypes = {
  inventory: Inventory.isRequired,
};

export default withI18n()(InventoryDetail);
