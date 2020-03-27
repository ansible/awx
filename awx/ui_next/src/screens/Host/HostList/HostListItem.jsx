import React, { Fragment } from 'react';
import { string, bool, func } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Button,
  DataListAction as _DataListAction,
  DataListCheck,
  DataListItem,
  DataListItemRow,
  DataListItemCells,
  Tooltip,
} from '@patternfly/react-core';
import DataListCell from '@components/DataListCell';

import { Link } from 'react-router-dom';
import { PencilAltIcon } from '@patternfly/react-icons';

import Sparkline from '@components/Sparkline';
import { Host } from '@types';
import styled from 'styled-components';
import HostToggle from '@components/HostToggle';

const DataListAction = styled(_DataListAction)`
  align-items: center;
  display: grid;
  grid-gap: 24px;
  grid-template-columns: 92px 40px;
`;

function HostListItem({ i18n, host, isSelected, onSelect, detailUrl }) {
  const labelId = `check-action-${host.id}`;
  const recentPlaybookJobs = host.summary_fields.recent_jobs.map(job => ({
    ...job,
    type: 'job',
  }));

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
              {host.summary_fields.inventory && (
                <Fragment>
                  <b css="margin-right: 24px">{i18n._(t`Inventory`)}</b>
                  <Link
                    to={`/inventories/${
                      host.summary_fields.inventory.kind === 'smart'
                        ? 'smart_inventory'
                        : 'inventory'
                    }/${host.summary_fields.inventory.id}/details`}
                  >
                    {host.summary_fields.inventory.name}
                  </Link>
                </Fragment>
              )}
            </DataListCell>,
          ]}
        />
        <DataListAction
          aria-label="actions"
          aria-labelledby={labelId}
          id={labelId}
        >
          <HostToggle host={host} />
          {host.summary_fields.user_capabilities.edit ? (
            <Tooltip content={i18n._(t`Edit Host`)} position="top">
              <Button
                aria-label={i18n._(t`Edit Host`)}
                variant="plain"
                component={Link}
                to={`/hosts/${host.id}/edit`}
              >
                <PencilAltIcon />
              </Button>
            </Tooltip>
          ) : (
            ''
          )}
        </DataListAction>
      </DataListItemRow>
    </DataListItem>
  );
}

HostListItem.propTypes = {
  host: Host.isRequired,
  detailUrl: string.isRequired,
  isSelected: bool.isRequired,
  onSelect: func.isRequired,
};

export default withI18n()(HostListItem);
