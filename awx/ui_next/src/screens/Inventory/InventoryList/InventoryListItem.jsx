import React from 'react';
import { string, bool, func } from 'prop-types';
import { withI18n } from '@lingui/react';
import {
  Button,
  DataListCheck,
  DataListItem,
  DataListItemRow,
  DataListItemCells,
  Tooltip,
} from '@patternfly/react-core';
import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';
import { PencilAltIcon } from '@patternfly/react-icons';

import DataListCell from '@components/DataListCell';
import { Inventory } from '@types';

class InventoryListItem extends React.Component {
  static propTypes = {
    inventory: Inventory.isRequired,
    detailUrl: string.isRequired,
    isSelected: bool.isRequired,
    onSelect: func.isRequired,
  };

  render() {
    const { inventory, isSelected, onSelect, detailUrl, i18n } = this.props;
    const labelId = `check-action-${inventory.id}`;
    return (
      <DataListItem
        key={inventory.id}
        aria-labelledby={labelId}
        id={`${inventory.id}`}
      >
        <DataListItemRow>
          <DataListCheck
            id={`select-inventory-${inventory.id}`}
            checked={isSelected}
            onChange={onSelect}
            aria-labelledby={labelId}
          />
          <DataListItemCells
            dataListCells={[
              <DataListCell key="divider">
                <Link to={`${detailUrl}`}>
                  <b>{inventory.name}</b>
                </Link>
              </DataListCell>,
              <DataListCell key="kind">
                {inventory.kind === 'smart'
                  ? i18n._(t`Smart Inventory`)
                  : i18n._(t`Inventory`)}
              </DataListCell>,
              <DataListCell key="edit" alignRight isFilled={false}>
                {inventory.summary_fields.user_capabilities.edit && (
                  <Tooltip content={i18n._(t`Edit Inventory`)} position="top">
                    <Button
                      variant="plain"
                      component={Link}
                      to={`/inventories/${
                        inventory.kind === 'smart'
                          ? 'smart_inventory'
                          : 'inventory'
                      }/${inventory.id}/edit`}
                    >
                      <PencilAltIcon />
                    </Button>
                  </Tooltip>
                )}
              </DataListCell>,
            ]}
          />
        </DataListItemRow>
      </DataListItem>
    );
  }
}
export default withI18n()(InventoryListItem);
