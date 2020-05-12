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

import HostToggle from '../../../components/HostToggle';
import Sparkline from '../../../components/Sparkline';
import { Host } from '../../../types';

const DataListAction = styled(_DataListAction)`
  align-items: center;
  display: grid;
  grid-gap: 24px;
  grid-template-columns: min-content 40px;
`;

function InventoryGroupHostListItem({
  i18n,
  detailUrl,
  editUrl,
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
          ]}
        />
        <DataListAction
          aria-label="actions"
          aria-labelledby={labelId}
          id={labelId}
        >
          <HostToggle css="grid-column: 1" host={host} />
          {host.summary_fields.user_capabilities?.edit && (
            <Tooltip content={i18n._(t`Edit Host`)} position="top">
              <Button
                aria-label={i18n._(t`Edit Host`)}
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

InventoryGroupHostListItem.propTypes = {
  detailUrl: string.isRequired,
  editUrl: string.isRequired,
  host: Host.isRequired,
  isSelected: bool.isRequired,
  onSelect: func.isRequired,
};

export default withI18n()(InventoryGroupHostListItem);
