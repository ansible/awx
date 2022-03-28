import React from 'react';
import { Link } from 'react-router-dom';
import { string, bool, func } from 'prop-types';

import { t } from '@lingui/macro';
import 'styled-components/macro';

import { Tr, Td } from '@patternfly/react-table';
import Sparkline from 'components/Sparkline';
import { Host } from 'types';

function SmartInventoryHostListItem({
  detailUrl,
  host,
  isSelected,
  onSelect,
  rowIndex,
}) {
  const recentPlaybookJobs = host.summary_fields.recent_jobs.map((job) => ({
    ...job,
    type: 'job',
  }));

  return (
    <Tr id={`host-row-${host.id}`} ouiaId={`host-row-${host.id}`}>
      <Td
        select={{
          rowIndex,
          isSelected,
          onSelect,
        }}
      />
      <Td dataLabel={t`Name`}>
        <Link to={`${detailUrl}`}>
          <b>{host.name}</b>
        </Link>
      </Td>
      <Td dataLabel={t`Recent jobs`}>
        <Sparkline jobs={recentPlaybookJobs} />
      </Td>
      <Td dataLabel={t`Inventory`}>
        <Link
          to={`/inventories/inventory/${host.summary_fields.inventory.id}/details`}
        >
          {host.summary_fields.inventory.name}
        </Link>
      </Td>
    </Tr>
  );
}

SmartInventoryHostListItem.propTypes = {
  detailUrl: string.isRequired,
  host: Host.isRequired,
  isSelected: bool.isRequired,
  onSelect: func.isRequired,
};

export default SmartInventoryHostListItem;
