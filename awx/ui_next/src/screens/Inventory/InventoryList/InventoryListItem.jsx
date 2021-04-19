import React, { useState, useCallback } from 'react';
import { string, bool, func } from 'prop-types';

import { Button, Label } from '@patternfly/react-core';
import { Tr, Td } from '@patternfly/react-table';
import { PencilAltIcon } from '@patternfly/react-icons';
import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';
import { timeOfDay } from '../../../util/dates';
import { InventoriesAPI } from '../../../api';
import { Inventory } from '../../../types';
import { ActionsTd, ActionItem } from '../../../components/PaginatedTable';
import CopyButton from '../../../components/CopyButton';
import StatusLabel from '../../../components/StatusLabel';

function InventoryListItem({
  inventory,
  rowIndex,
  isSelected,
  onSelect,
  detailUrl,

  fetchInventories,
}) {
  InventoryListItem.propTypes = {
    inventory: Inventory.isRequired,
    detailUrl: string.isRequired,
    isSelected: bool.isRequired,
    onSelect: func.isRequired,
  };
  const [isCopying, setIsCopying] = useState(false);

  const copyInventory = useCallback(async () => {
    await InventoriesAPI.copy(inventory.id, {
      name: `${inventory.name} @ ${timeOfDay()}`,
    });
    await fetchInventories();
  }, [inventory.id, inventory.name, fetchInventories]);

  const handleCopyStart = useCallback(() => {
    setIsCopying(true);
  }, []);

  const handleCopyFinish = useCallback(() => {
    setIsCopying(false);
  }, []);

  const labelId = `check-action-${inventory.id}`;

  let syncStatus = 'disabled';
  if (inventory.isSourceSyncRunning) {
    syncStatus = 'syncing';
  } else if (inventory.has_inventory_sources) {
    syncStatus =
      inventory.inventory_sources_with_failures > 0 ? 'error' : 'success';
  }

  let tooltipContent = '';
  if (inventory.has_inventory_sources) {
    if (inventory.inventory_sources_with_failures > 0) {
      tooltipContent = t`${inventory.inventory_sources_with_failures} sources with sync failures.`;
    } else {
      tooltipContent = t`No inventory sync failures.`;
    }
  } else {
    tooltipContent = t`Not configured for inventory sync.`;
  }

  return (
    <Tr id={inventory.id} aria-labelledby={labelId}>
      <Td
        select={{
          rowIndex,
          isSelected,
          onSelect,
        }}
        dataLabel={t`Selected`}
      />
      <Td id={labelId} dataLabel={t`Name`}>
        {inventory.pending_deletion ? (
          <b>{inventory.name}</b>
        ) : (
          <Link to={`${detailUrl}`}>
            <b>{inventory.name}</b>
          </Link>
        )}
      </Td>
      <Td dataLabel={t`Status`}>
        {inventory.kind !== 'smart' && (
          <StatusLabel status={syncStatus} tooltipContent={tooltipContent} />
        )}
      </Td>
      <Td dataLabel={t`Type`}>
        {inventory.kind === 'smart' ? t`Smart Inventory` : t`Inventory`}
      </Td>
      <Td key="organization" dataLabel={t`Organization`}>
        <Link
          to={`/organizations/${inventory?.summary_fields?.organization?.id}/details`}
        >
          {inventory?.summary_fields?.organization?.name}
        </Link>
      </Td>
      {inventory.pending_deletion ? (
        <Td dataLabel={t`Groups`}>
          <Label color="red">{t`Pending delete`}</Label>
        </Td>
      ) : (
        <ActionsTd dataLabel={t`Actions`}>
          <ActionItem
            visible={inventory.summary_fields.user_capabilities.edit}
            tooltip={t`Edit Inventory`}
          >
            <Button
              ouiaId={`${inventory.id}-edit-button`}
              isDisabled={isCopying}
              aria-label={t`Edit Inventory`}
              variant="plain"
              component={Link}
              to={`/inventories/${
                inventory.kind === 'smart' ? 'smart_inventory' : 'inventory'
              }/${inventory.id}/edit`}
            >
              <PencilAltIcon />
            </Button>
          </ActionItem>
          <ActionItem
            visible={inventory.summary_fields.user_capabilities.copy}
            tooltip={
              inventory.has_inventory_sources
                ? t`Inventories with sources cannot be copied`
                : t`Copy Inventory`
            }
          >
            <CopyButton
              copyItem={copyInventory}
              isDisabled={isCopying || inventory.has_inventory_sources}
              onCopyStart={handleCopyStart}
              onCopyFinish={handleCopyFinish}
              errorMessage={t`Failed to copy inventory.`}
            />
          </ActionItem>
        </ActionsTd>
      )}
    </Tr>
  );
}
export default InventoryListItem;
