import React from 'react';
import { bool, func, number, oneOfType, string } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import {
  Button,
  DataListAction,
  DataListCheck,
  DataListItem,
  DataListItemCells,
  DataListItemRow,
  Tooltip,
} from '@patternfly/react-core';

import { Link } from 'react-router-dom';
import { PencilAltIcon } from '@patternfly/react-icons';
import DataListCell from '../../../components/DataListCell';
import { Group } from '../../../types';

function InventoryHostGroupItem({
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
    <DataListItem key={group.id} aria-labelledby={labelId} id={`${group.id}`}>
      <DataListItemRow>
        <DataListCheck
          aria-labelledby={labelId}
          id={`select-group-${group.id}`}
          checked={isSelected}
          onChange={onSelect}
        />
        <DataListItemCells
          dataListCells={[
            <DataListCell key="name">
              <Link to={`${detailUrl}`} id={labelId}>
                <b>{group.name}</b>
              </Link>
            </DataListCell>,
          ]}
        />
        <DataListAction
          aria-label="actions"
          aria-labelledby={labelId}
          id={labelId}
        >
          {group.summary_fields.user_capabilities.edit && (
            <Tooltip content={i18n._(t`Edit Group`)} position="top">
              <Button variant="plain" component={Link} to={editUrl}>
                <PencilAltIcon />
              </Button>
            </Tooltip>
          )}
        </DataListAction>
      </DataListItemRow>
    </DataListItem>
  );
}

InventoryHostGroupItem.propTypes = {
  group: Group.isRequired,
  inventoryId: oneOfType([number, string]).isRequired,
  isSelected: bool.isRequired,
  onSelect: func.isRequired,
};

export default withI18n()(InventoryHostGroupItem);
