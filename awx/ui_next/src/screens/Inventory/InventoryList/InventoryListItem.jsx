import React, { useState, useCallback } from 'react';
import { string, bool, func } from 'prop-types';
import { withI18n } from '@lingui/react';
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
  i18n,
  fetchInventories,
}) {
  InventoryListItem.propTypes = {
    inventory: Inventory.isRequired,
    detailUrl: string.isRequired,
    isSelected: bool.isRequired,
    onSelect: func.isRequired,
  };
  const [isDisabled, setIsDisabled] = useState(false);

  const copyInventory = useCallback(async () => {
    await InventoriesAPI.copy(inventory.id, {
      name: `${inventory.name} @ ${timeOfDay()}`,
    });
    await fetchInventories();
  }, [inventory.id, inventory.name, fetchInventories]);

  const handleCopyStart = useCallback(() => {
    setIsDisabled(true);
  }, []);

  const handleCopyFinish = useCallback(() => {
    setIsDisabled(false);
  }, []);

  const labelId = `check-action-${inventory.id}`;

  let syncStatus = 'disabled';
  if (inventory.isSourceSyncRunning) {
    syncStatus = 'syncing';
  } else if (inventory.has_inventory_sources) {
    syncStatus =
      inventory.inventory_sources_with_failures > 0 ? 'error' : 'success';
  }

  return (
    <Tr id={inventory.id}>
      <Td
        select={{
          rowIndex,
          isSelected,
          onSelect,
        }}
      />
      <Td id={labelId}>
        {inventory.pending_deletion ? (
          <b>{inventory.name}</b>
        ) : (
          <Link to={`${detailUrl}`}>
            <b>{inventory.name}</b>
          </Link>
        )}
      </Td>
      <Td>
        {inventory.kind !== 'smart' && <StatusLabel status={syncStatus} />}
      </Td>
      <Td>
        {inventory.kind === 'smart'
          ? i18n._(t`Smart Inventory`)
          : i18n._(t`Inventory`)}
      </Td>
      <Td key="organization">
        <Link
          to={`/organizations/${inventory.summary_fields.organization.id}/details`}
        >
          {inventory.summary_fields.organization.name}
        </Link>
      </Td>
      <Td>{inventory.total_groups}</Td>
      <Td>{inventory.total_hosts}</Td>
      <Td>{inventory.total_inventory_sources}</Td>
      {inventory.pending_deletion ? (
        <Td>
          <Label color="red">{i18n._(t`Pending delete`)}</Label>
        </Td>
      ) : (
        <ActionsTd>
          <ActionItem
            visible={inventory.summary_fields.user_capabilities.edit}
            tooltip={i18n._(t`Edit Inventory`)}
          >
            <Button
              isDisabled={isDisabled}
              aria-label={i18n._(t`Edit Inventory`)}
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
            tooltip={i18n._(t`Copy Inventory`)}
          >
            <CopyButton
              copyItem={copyInventory}
              isDisabled={isDisabled}
              onCopyStart={handleCopyStart}
              onCopyFinish={handleCopyFinish}
              helperText={{
                tooltip: i18n._(t`Copy Inventory`),
                errorMessage: i18n._(t`Failed to copy inventory.`),
              }}
            />
          </ActionItem>
        </ActionsTd>
      )}
    </Tr>
  );
}
export default withI18n()(InventoryListItem);
