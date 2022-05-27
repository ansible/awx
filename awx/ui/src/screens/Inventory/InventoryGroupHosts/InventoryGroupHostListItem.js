import 'styled-components/macro';
import React from 'react';
import { Link } from 'react-router-dom';
import { string, bool, func, number } from 'prop-types';
import { t } from '@lingui/macro';
import { Button, Tooltip } from '@patternfly/react-core';
import { PencilAltIcon } from '@patternfly/react-icons';

import { Td, Tr } from '@patternfly/react-table';
import { ActionItem, ActionsTd } from 'components/PaginatedTable';
import HostToggle from 'components/HostToggle';
import Sparkline from 'components/Sparkline';
import { Host } from 'types';

function InventoryGroupHostListItem({
  detailUrl,
  editUrl,
  host,
  rowIndex,
  isSelected,
  onSelect,
}) {
  const recentPlaybookJobs = host.summary_fields.recent_jobs.map((job) => ({
    ...job,
    type: 'job',
  }));

  const labelId = `check-action-${host.id}`;

  return (
    <Tr
      id={host.id}
      ouiaId={`inventory-group-host-row-${host.id}`}
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
      <Td dataLabel={t`host-name-${host.id}`} id={labelId}>
        <Link to={`${detailUrl}`}>
          <b>{host.name}</b>
        </Link>
      </Td>
      <Td dataLabel={t`host-description-${host.id}`}>{host.description}</Td>
      <Td dataLabel={t`Activity`}>
        <Sparkline jobs={recentPlaybookJobs} />
      </Td>
      <ActionsTd dataLabel={t`Actions`} gridColumns="auto 40px">
        <ActionItem
          visible={host.summary_fields.user_capabilities?.edit}
          tooltip={t`Toggle host`}
        >
          <HostToggle host={host} />
        </ActionItem>
        <ActionItem
          tooltip={t`Edit Host`}
          visible={host.summary_fields.user_capabilities?.edit}
        >
          <Tooltip content={t`Edit Host`} position="top">
            <Button
              ouiaId={`${host.id}-edit-button`}
              aria-label={t`Edit Host`}
              variant="plain"
              component={Link}
              to={`${editUrl}`}
            >
              <PencilAltIcon />
            </Button>
          </Tooltip>
        </ActionItem>
      </ActionsTd>
    </Tr>
  );
}

InventoryGroupHostListItem.propTypes = {
  detailUrl: string.isRequired,
  editUrl: string.isRequired,
  rowIndex: number.isRequired,
  host: Host.isRequired,
  isSelected: bool.isRequired,
  onSelect: func.isRequired,
};

export default InventoryGroupHostListItem;
