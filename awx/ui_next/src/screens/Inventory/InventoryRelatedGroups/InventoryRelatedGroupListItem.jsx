import 'styled-components/macro';
import React from 'react';
import { Link } from 'react-router-dom';
import { string, bool, func } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import {
  Button,
  DataListAction as _DataListAction,
  DataListCheck,
  DataListItem,
  DataListItemCells,
  DataListItemRow,
  Tooltip,
} from '@patternfly/react-core';
import { PencilAltIcon } from '@patternfly/react-icons';
import styled from 'styled-components';
import DataListCell from '../../../components/DataListCell';

import { Group } from '../../../types';

const DataListAction = styled(_DataListAction)`
  align-items: center;
  display: grid;
  grid-gap: 24px;
  grid-template-columns: min-content 40px;
`;

function InventoryRelatedGroupListItem({
  i18n,
  detailUrl,
  editUrl,
  group,
  isSelected,
  onSelect,
}) {
  const labelId = `check-action-${group.id}`;

  return (
    <DataListItem key={group.id} aria-labelledby={labelId} id={`${group.id}`}>
      <DataListItemRow>
        <DataListCheck
          id={`select-group-${group.id}`}
          checked={isSelected}
          onChange={onSelect}
          aria-labelledby={labelId}
        />
        <DataListItemCells
          dataListCells={[
            <DataListCell key="name">
              <Link to={`${detailUrl}`}>
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
          {group.summary_fields.user_capabilities?.edit && (
            <Tooltip content={i18n._(t`Edit Group`)} position="top">
              <Button
                aria-label={i18n._(t`Edit Group`)}
                css="grid-column: 2"
                variant="plain"
                component={Link}
                to={`${editUrl}`}
              >
                <PencilAltIcon />
              </Button>
            </Tooltip>
          )}
        </DataListAction>
      </DataListItemRow>
    </DataListItem>
  );
}

InventoryRelatedGroupListItem.propTypes = {
  detailUrl: string.isRequired,
  editUrl: string.isRequired,
  group: Group.isRequired,
  isSelected: bool.isRequired,
  onSelect: func.isRequired,
};

export default withI18n()(InventoryRelatedGroupListItem);
