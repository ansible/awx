import React from 'react';
import { string, bool, func } from 'prop-types';
import { t } from '@lingui/macro';
import { Button } from '@patternfly/react-core';
import { Tr, Td } from '@patternfly/react-table';
import { Link } from 'react-router-dom';
import { PencilAltIcon } from '@patternfly/react-icons';
import { ActionsTd, ActionItem, TdBreakWord } from 'components/PaginatedTable';

import HostToggle from 'components/HostToggle';
import { Host } from 'types';

function InventoryHostItem({
  detailUrl,
  editUrl,
  host,
  isSelected,
  onSelect,
  rowIndex,
}) {
  const labelId = `check-action-${host.id}`;

  return (
    <Tr id={`host-row-${host.id}`} ouiaId={`inventory-host-row-${host.id}`}>
      <Td
        data-cy={labelId}
        select={{
          rowIndex,
          isSelected,
          onSelect,
        }}
      />
      <TdBreakWord id={labelId} dataLabel={t`Name`}>
        <Link to={`${detailUrl}`}>
          <b>{host.name}</b>
        </Link>
      </TdBreakWord>
      <TdBreakWord
        id={`host-description-${host.id}`}
        dataLabel={t`Description`}
      >
        {host.description}
      </TdBreakWord>
      <ActionsTd dataLabel={t`Actions`} gridColumns="auto 40px">
        <HostToggle host={host} />
        <ActionItem
          visible={host.summary_fields.user_capabilities?.edit}
          tooltip={t`Edit host`}
        >
          <Button
            ouiaId={`${host.id}-edit-button`}
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

InventoryHostItem.propTypes = {
  detailUrl: string.isRequired,
  host: Host.isRequired,
  isSelected: bool.isRequired,
  onSelect: func.isRequired,
};

export default InventoryHostItem;
