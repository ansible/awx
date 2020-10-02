import React, { useState, useCallback } from 'react';
import { string, bool, func } from 'prop-types';
import { withI18n } from '@lingui/react';
import {
  Button,
  DataListAction as _DataListAction,
  DataListCheck,
  DataListItem,
  DataListItemCells,
  DataListItemRow,
  Label,
  Tooltip,
} from '@patternfly/react-core';
import { PencilAltIcon } from '@patternfly/react-icons';
import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';
import styled from 'styled-components';
import { timeOfDay } from 'util/dates';
import { InventoriesAPI } from 'api';
import { Inventory } from 'types';
import DataListCell from 'components/DataListCell';
import CopyButton from 'components/CopyButton';
import SyncStatusIndicator from 'components/SyncStatusIndicator';

const DataListAction = styled(_DataListAction)`
  align-items: center;
  display: grid;
  grid-gap: 16px;
  grid-template-columns: repeat(2, 40px);
`;

function InventoryListItem({
  inventory,
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
    <DataListItem
      key={inventory.id}
      aria-labelledby={labelId}
      id={`${inventory.id}`}
    >
      <DataListItemRow>
        <DataListCheck
          id={`select-inventory-${inventory.id}`}
          isDisabled={inventory.pending_deletion}
          checked={isSelected}
          onChange={onSelect}
          aria-labelledby={labelId}
        />
        <DataListItemCells
          dataListCells={[
            <DataListCell key="sync-status" isIcon>
              <SyncStatusIndicator status={syncStatus} />
            </DataListCell>,
            <DataListCell key="name">
              {inventory.pending_deletion ? (
                <b>{inventory.name}</b>
              ) : (
                <Link to={`${detailUrl}`}>
                  <b>{inventory.name}</b>
                </Link>
              )}
            </DataListCell>,
            <DataListCell key="kind">
              {inventory.kind === 'smart'
                ? i18n._(t`Smart Inventory`)
                : i18n._(t`Inventory`)}
            </DataListCell>,
            inventory.pending_deletion && (
              <DataListCell alignRight isFilled={false} key="pending-delete">
                <Label color="red">{i18n._(t`Pending delete`)}</Label>
              </DataListCell>
            ),
          ]}
        />
        {!inventory.pending_deletion && (
          <DataListAction
            aria-label="actions"
            aria-labelledby={labelId}
            id={labelId}
          >
            {inventory.summary_fields.user_capabilities.edit ? (
              <Tooltip content={i18n._(t`Edit Inventory`)} position="top">
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
              </Tooltip>
            ) : (
              ''
            )}
            {inventory.summary_fields.user_capabilities.copy && (
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
            )}
          </DataListAction>
        )}
      </DataListItemRow>
    </DataListItem>
  );
}
export default withI18n()(InventoryListItem);
