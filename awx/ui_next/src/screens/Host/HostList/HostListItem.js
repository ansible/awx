import 'styled-components/macro';
import React, { useState } from 'react';
import { string, bool, func } from 'prop-types';

import { t } from '@lingui/macro';
import { Button } from '@patternfly/react-core';
import { Tr, Td, ExpandableRowContent } from '@patternfly/react-table';
import { Link } from 'react-router-dom';
import { PencilAltIcon } from '@patternfly/react-icons';
import { ActionsTd, ActionItem } from 'components/PaginatedTable';
import { Host } from 'types';
import HostToggle from 'components/HostToggle';
import { DetailList, Detail } from 'components/DetailList';
import Sparkline from 'components/Sparkline';

function HostListItem({ host, isSelected, onSelect, detailUrl, rowIndex }) {
  const labelId = `check-action-${host.id}`;
  const [isExpanded, setIsExpanded] = useState(false);

  const {
    summary_fields: { recent_jobs: recentJobs = [] },
  } = host;

  return (
    <>
      <Tr id={`host-row-${host.id}`}>
        <Td
          expand={{
            rowIndex,
            isExpanded,
            onToggle: () => setIsExpanded(!isExpanded),
          }}
        />
        <Td
          data-cy={labelId}
          select={{
            rowIndex,
            isSelected,
            onSelect,
          }}
          dataLabel={t`Selected`}
        />
        <Td id={labelId} dataLabel={t`Name`}>
          <Link to={`${detailUrl}`}>
            <b>{host.name}</b>
          </Link>
        </Td>
        <Td dataLabel={t`Inventory`}>
          {host.summary_fields.inventory && (
            <Link
              to={`/inventories/inventory/${host.summary_fields.inventory.id}/details`}
            >
              {host.summary_fields.inventory.name}
            </Link>
          )}
        </Td>
        <ActionsTd dataLabel={t`Actions`} gridColumns="auto 40px">
          <HostToggle host={host} />
          <ActionItem
            visible={host.summary_fields.user_capabilities.edit}
            tooltip={t`Edit Host`}
          >
            <Button
              ouiaId={`${host.id}-edit-button}`}
              aria-label={t`Edit Host`}
              variant="plain"
              component={Link}
              to={`/hosts/${host.id}/edit`}
            >
              <PencilAltIcon />
            </Button>
          </ActionItem>
        </ActionsTd>
      </Tr>
      <Tr isExpanded={isExpanded}>
        <Td colSpan={2} />
        <Td colSpan={4}>
          <ExpandableRowContent>
            <DetailList gutter="sm">
              <Detail
                label={t`Activity`}
                value={
                  recentJobs.length > 0 ? (
                    <Sparkline jobs={recentJobs} />
                  ) : (
                    t`No job data available`
                  )
                }
              />
            </DetailList>
          </ExpandableRowContent>
        </Td>
      </Tr>
    </>
  );
}

HostListItem.propTypes = {
  host: Host.isRequired,
  detailUrl: string.isRequired,
  isSelected: bool.isRequired,
  onSelect: func.isRequired,
};

export default HostListItem;
