import React from 'react';
import { Link } from 'react-router-dom';
import { string, bool, func } from 'prop-types';

import { t } from '@lingui/macro';
import 'styled-components/macro';

import { Tr, Td } from '@patternfly/react-table';
import Sparkline from 'components/Sparkline';
import { Host } from 'types';

function AdvancedInventoryHostListItem({
  detailUrl,
  host: {
    name,
    id,
    summary_fields: { recent_jobs, inventory },
  },
  isSelected,
  onSelect,
  rowIndex,
  inventoryType,
}) {
  const recentPlaybookJobs = recent_jobs.map((job) => ({
    ...job,
    type: 'job',
  }));
  const inventoryKind = inventory.kind === '' ? 'inventory' : inventoryType;
  const inventoryLink = `/inventories/${inventoryKind}/${inventory.id}/details`;
  return (
    <Tr id={`host-row-${id}`} ouiaId={`host-row-${id}`}>
      <Td
        select={{
          rowIndex,
          isSelected,
          onSelect,
        }}
      />
      <Td dataLabel={t`Name`}>
        <Link to={`${detailUrl}`}>
          <b>{name}</b>
        </Link>
      </Td>
      <Td dataLabel={t`Recent jobs`}>
        <Sparkline jobs={recentPlaybookJobs} />
      </Td>
      <Td dataLabel={t`Inventory`}>
        <Link to={inventoryLink}>{inventory.name}</Link>
      </Td>
    </Tr>
  );
}

AdvancedInventoryHostListItem.propTypes = {
  detailUrl: string.isRequired,
  host: Host.isRequired,
  isSelected: bool.isRequired,
  onSelect: func.isRequired,
};

export default AdvancedInventoryHostListItem;
