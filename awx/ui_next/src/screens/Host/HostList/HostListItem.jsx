import React, { Fragment } from 'react';
import { string, bool, func } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  DataListItem,
  DataListItemRow,
  DataListItemCells,
  Tooltip,
} from '@patternfly/react-core';
import { Link } from 'react-router-dom';
import { PencilAltIcon } from '@patternfly/react-icons';

import ActionButtonCell from '@components/ActionButtonCell';
import DataListCell from '@components/DataListCell';
import DataListCheck from '@components/DataListCheck';
import ListActionButton from '@components/ListActionButton';
import { Sparkline } from '@components/Sparkline';
import Switch from '@components/Switch';
import VerticalSeparator from '@components/VerticalSeparator';
import { Host } from '@types';

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
      toggleHost,
      toggleLoading,
      i18n,
    } = this.props;
    const labelId = `check-action-${host.id}`;
    return (
      <DataListItem key={host.id} aria-labelledby={labelId}>
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
                <VerticalSeparator />
                <Link to={`${detailUrl}`}>
                  <b>{host.name}</b>
                </Link>
              </DataListCell>,
              <DataListCell key="recentJobs">
                <Sparkline jobs={host.summary_fields.recent_jobs} />
              </DataListCell>,
              <DataListCell key="inventory">
                {host.summary_fields.inventory && (
                  <Fragment>
                    <b style={{ marginRight: '20px' }}>
                      {i18n._(t`Inventory`)}
                    </b>
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
              <ActionButtonCell lastcolumn="true" key="action">
                <Tooltip
                  content={i18n._(
                    t`Indicates if a host is available and should be included in running jobs.  For hosts that are part of an external inventory, this may be reset by the inventory sync process.`
                  )}
                  position="top"
                >
                  <Switch
                    id={`host-${host.id}-toggle`}
                    label={i18n._(t`On`)}
                    labelOff={i18n._(t`Off`)}
                    isChecked={host.enabled}
                    isDisabled={
                      toggleLoading ||
                      !host.summary_fields.user_capabilities.edit
                    }
                    onChange={() => toggleHost(host)}
                    aria-label={i18n._(t`Toggle host`)}
                  />
                </Tooltip>
                {host.summary_fields.user_capabilities.edit && (
                  <Tooltip content={i18n._(t`Edit Host`)} position="top">
                    <ListActionButton
                      variant="plain"
                      component={Link}
                      to={`/hosts/${host.id}/edit`}
                    >
                      <PencilAltIcon />
                    </ListActionButton>
                  </Tooltip>
                )}
              </ActionButtonCell>,
            ]}
          />
        </DataListItemRow>
      </DataListItem>
    );
  }
}
export default withI18n()(HostListItem);
