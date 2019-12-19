import React from 'react';
import { bool, func, number, oneOfType, string } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Group } from '@types';

import {
  DataListItem,
  DataListItemRow,
  DataListItemCells,
  Tooltip,
} from '@patternfly/react-core';
import { Link } from 'react-router-dom';
import { PencilAltIcon } from '@patternfly/react-icons';

import ActionButtonCell from '@components/ActionButtonCell';
import DataListCell from '@components/DataListCell';
import DataListCheck from '@components/DataListCheck';
import ListActionButton from '@components/ListActionButton';
import VerticalSeparator from '@components/VerticalSeparator';

function InventoryGroupItem({
  i18n,
  group,
  inventoryId,
  isSelected,
  onSelect,
}) {
  const labelId = `check-action-${group.id}`;
  const detailUrl = `/inventories/inventory/${inventoryId}/groups/${group.id}/details`;
  const editUrl = `/inventories/inventory/${inventoryId}/groups/${group.id}/edit`;

  return (
    <DataListItem key={group.id} aria-labelledby={labelId}>
      <DataListItemRow>
        <DataListCheck
          aria-labelledby={labelId}
          id={`select-group-${group.id}`}
          checked={isSelected}
          onChange={onSelect}
        />
        <DataListItemCells
          dataListCells={[
            <DataListCell key="divider">
              <VerticalSeparator />
              <Link to={`${detailUrl}`} id={labelId}>
                <b>{group.name}</b>
              </Link>
            </DataListCell>,
            <ActionButtonCell lastcolumn="true" key="action">
              {group.summary_fields.user_capabilities.edit && (
                <Tooltip content={i18n._(t`Edit Group`)} position="top">
                  <ListActionButton
                    variant="plain"
                    component={Link}
                    to={editUrl}
                  >
                    <PencilAltIcon />
                  </ListActionButton>
                </Tooltip>
              )}
            </ActionButtonCell>,
          ]}
        />
      </DataListItemRow>
    </DataListItem>
  );
}

InventoryGroupItem.propTypes = {
  group: Group.isRequired,
  inventoryId: oneOfType([number, string]).isRequired,
  isSelected: bool.isRequired,
  onSelect: func.isRequired,
};

export default withI18n()(InventoryGroupItem);
