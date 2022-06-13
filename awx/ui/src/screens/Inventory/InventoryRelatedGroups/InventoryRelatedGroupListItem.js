import 'styled-components/macro';
import React from 'react';
import { Link } from 'react-router-dom';
import { string, bool, func, number } from 'prop-types';

import { t } from '@lingui/macro';

import { Td, Tr } from '@patternfly/react-table';
import { Button } from '@patternfly/react-core';
import { PencilAltIcon } from '@patternfly/react-icons';

import { Group } from 'types';
import { ActionItem, ActionsTd } from 'components/PaginatedTable';

function InventoryRelatedGroupListItem({
  detailUrl,
  editUrl,
  group,
  rowIndex,
  isSelected,
  onSelect,
}) {
  const labelId = `check-action-${group.id}`;

  return (
    <Tr
      id={group.id}
      ouiaId={`group-row-${group.id}`}
      aria-labelledby={labelId}
    >
      <Td
        select={{
          rowIndex,
          isSelected,
          onSelect,
        }}
        dataLabel={t`Selected`}
      />
      <Td id={labelId}>
        <Link to={`${detailUrl}`}>
          <b>{group.name}</b>
        </Link>
      </Td>
      <ActionsTd dataLabel={t`Actions`}>
        <ActionItem
          tooltip={t`Edit Group`}
          visible={group.summary_fields.user_capabilities?.edit}
        >
          <Button
            ouiaId={`${group.id}-edit-button`}
            aria-label={t`Edit Group`}
            variant="plain"
            component={Link}
            to={`${editUrl}`}
          >
            <PencilAltIcon />
          </Button>
        </ActionItem>
      </ActionsTd>
    </Tr>
  );
}

InventoryRelatedGroupListItem.propTypes = {
  detailUrl: string.isRequired,
  editUrl: string.isRequired,
  group: Group.isRequired,
  rowIndex: number.isRequired,
  isSelected: bool.isRequired,
  onSelect: func.isRequired,
};

export default InventoryRelatedGroupListItem;
