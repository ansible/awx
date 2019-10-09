import React from 'react';
import { string, bool, func } from 'prop-types';
import { withI18n } from '@lingui/react';
import {
  DataListItem,
  DataListItemRow,
  DataListItemCells,
} from '@patternfly/react-core';
import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';

import DataListCell from '@components/DataListCell';
import DataListCheck from '@components/DataListCheck';
import VerticalSeparator from '@components/VerticalSeparator';
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
      <DataListItem key={inventory.id} aria-labelledby={labelId}>
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
                <VerticalSeparator />
                <Link to={`${detailUrl}`}>
                  <b>{inventory.name}</b>
                </Link>
              </DataListCell>,
              <DataListCell key="kind">
                {inventory.kind === 'smart'
                  ? i18n._(t`Smart Inventory`)
                  : i18n._(t`Inventory`)}
              </DataListCell>,
            ]}
          />
        </DataListItemRow>
      </DataListItem>
    );
  }
}
export default withI18n()(InventoryListItem);
