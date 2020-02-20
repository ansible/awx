import React, { Fragment } from 'react';
import { string, bool, func } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Button,
  DataListAction as _DataListAction,
  DataListCell,
  DataListCheck,
  DataListItem,
  DataListItemRow,
  DataListItemCells,
  Switch,
  Tooltip,
} from '@patternfly/react-core';
import { Link } from 'react-router-dom';
import { PencilAltIcon } from '@patternfly/react-icons';

import Sparkline from '@components/Sparkline';
import { Host } from '@types';
import styled from 'styled-components';

const DataListAction = styled(_DataListAction)`
  align-items: center;
  display: grid;
  grid-gap: 24px;
  grid-template-columns: min-content 40px;
`;

class HostListItem extends React.Component {
  static propTypes = {
    host: Host.isRequired,
    detailUrl: string.isRequired,
    isSelected: bool.isRequired,
    onSelect: func.isRequired,
  };

  render() {
    const {
      host,
      isSelected,
      onSelect,
      detailUrl,
      onToggleHost,
      toggleLoading,
      i18n,
    } = this.props;

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
            <Tooltip
              content={i18n._(
                t`Indicates if a host is available and should be included in running jobs.  For hosts that are part of an external inventory, this may be reset by the inventory sync process.`
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
                  toggleLoading || !host.summary_fields.user_capabilities.edit
                }
                onChange={() => onToggleHost(host)}
                aria-label={i18n._(t`Toggle host`)}
              />
            </Tooltip>
            {host.summary_fields.user_capabilities.edit && (
              <Tooltip content={i18n._(t`Edit Host`)} position="top">
                <Button
                  variant="plain"
                  component={Link}
                  to={`/hosts/${host.id}/edit`}
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
}
export default withI18n()(HostListItem);
