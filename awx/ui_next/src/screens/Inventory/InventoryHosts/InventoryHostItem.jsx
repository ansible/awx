import React from 'react';
import { string, bool, func } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Button,
  DataListCheck,
  DataListItem,
  DataListItemRow,
  DataListItemCells,
  Switch,
  Tooltip,
} from '@patternfly/react-core';
import { Link } from 'react-router-dom';
import { PencilAltIcon } from '@patternfly/react-icons';

import DataListCell from '@components/DataListCell';
import { Sparkline } from '@components/Sparkline';
import { Host } from '@types';

function InventoryHostItem(props) {
  const {
    detailUrl,
    editUrl,
    host,
    i18n,
    isSelected,
    onSelect,
    toggleHost,
    toggleLoading,
  } = props;

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
            <DataListCell key="divider">
              <Link to={`${detailUrl}`}>
                <b>{host.name}</b>
              </Link>
            </DataListCell>,
            <DataListCell key="recentJobs">
              <Sparkline jobs={recentPlaybookJobs} />
            </DataListCell>,
            <DataListCell key="enable" alignRight isFilled={false}>
              <Tooltip
                content={i18n._(
                  t`Indicates if a host is available and should be included
                  in running jobs.  For hosts that are part of an external
                  inventory, this may be reset by the inventory sync process.`
                )}
                position="top"
              >
                <Switch
                  css="display: inline-flex;"
                  id={`host-${host.id}-toggle`}
                  label={i18n._(t`On`)}
                  labelOff={i18n._(t`Off`)}
                  isChecked={host.enabled}
                  isDisabled={
                    toggleLoading ||
                    !host.summary_fields.user_capabilities?.edit
                  }
                  onChange={() => toggleHost(host)}
                  aria-label={i18n._(t`Toggle host`)}
                />
              </Tooltip>
            </DataListCell>,
            <DataListCell key="edit" alignRight isFilled={false}>
              {host.summary_fields.user_capabilities?.edit && (
                <Tooltip content={i18n._(t`Edit Host`)} position="top">
                  <Button variant="plain" component={Link} to={`${editUrl}`}>
                    <PencilAltIcon />
                  </Button>
                </Tooltip>
              )}
            </DataListCell>,
          ]}
        />
      </DataListItemRow>
    </DataListItem>
  );
}

InventoryHostItem.propTypes = {
  detailUrl: string.isRequired,
  host: Host.isRequired,
  isSelected: bool.isRequired,
  onSelect: func.isRequired,
  toggleHost: func.isRequired,
  toggleLoading: bool.isRequired,
};

export default withI18n()(InventoryHostItem);
