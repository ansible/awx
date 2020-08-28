import React from 'react';
import { Link } from 'react-router-dom';
import { string, bool, func } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import 'styled-components/macro';

import {
  DataListCheck,
  DataListItem,
  DataListItemCells,
  DataListItemRow,
} from '@patternfly/react-core';
import DataListCell from '../../../components/DataListCell';
import Sparkline from '../../../components/Sparkline';
import { Host } from '../../../types';

function SmartInventoryHostListItem({
  i18n,
  detailUrl,
  host,
  isSelected,
  onSelect,
}) {
  const recentPlaybookJobs = host.summary_fields.recent_jobs.map(job => ({
    ...job,
    type: 'job',
  }));

  const labelId = `check-action-${host.id}`;

  return (
    <DataListItem key={host.id} aria-labelledby={labelId} id={`${host.id}`}>
      <DataListItemRow>
        <DataListCheck
          id={`select-host-${host.id}`}
          checked={isSelected}
          onChange={onSelect}
          aria-labelledby={labelId}
        />
        <DataListItemCells
          dataListCells={[
            <DataListCell key="name">
              <Link to={`${detailUrl}`}>
                <b>{host.name}</b>
              </Link>
            </DataListCell>,
            <DataListCell key="recentJobs">
              <Sparkline jobs={recentPlaybookJobs} />
            </DataListCell>,
            <DataListCell key="inventory">
              <>
                <b css="margin-right: 24px">{i18n._(t`Inventory`)}</b>
                <Link
                  to={`/inventories/inventory/${host.summary_fields.inventory.id}/details`}
                >
                  {host.summary_fields.inventory.name}
                </Link>
              </>
            </DataListCell>,
          ]}
        />
      </DataListItemRow>
    </DataListItem>
  );
}

SmartInventoryHostListItem.propTypes = {
  detailUrl: string.isRequired,
  host: Host.isRequired,
  isSelected: bool.isRequired,
  onSelect: func.isRequired,
};

export default withI18n()(SmartInventoryHostListItem);
