import React from 'react';
import { Trans } from '@lingui/macro';
import {
  Badge,
  DataListItem,
  DataListItemRow,
  DataListItemCells,
  DataListCheck,
  DataListCell,
} from '@patternfly/react-core';
import {
  Link
} from 'react-router-dom';

import VerticalSeparator from '../../../components/VerticalSeparator';

class OrganizationListItem extends React.Component {
  render () {
    const {
      itemId,
      name,
      memberCount,
      teamCount,
      isSelected,
      onSelect,
      detailUrl,
    } = this.props;
    const labelId = `check-action-${itemId}`;
    return (
      <DataListItem key={itemId} aria-labelledby={labelId}>
        <DataListItemRow>
          <DataListCheck
            id={`select-organization-${itemId}`}
            checked={isSelected}
            onChange={onSelect}
            aria-labelledby={labelId}
          />
          <DataListItemCells dataListCells={[
            <DataListCell key="divider" className="pf-c-data-list__cell--divider">
              <VerticalSeparator />
            </DataListCell>,
            <DataListCell key="org-name">
              <span id={labelId}>
                <Link
                  to={`${detailUrl}`}
                >
                  <b>{name}</b>
                </Link>
              </span>
            </DataListCell>,
            <DataListCell key="org-members" width={2}>
              <span className="awx-c-list-group">
                <Trans>Members</Trans>
                <Badge className="awx-c-list-group--badge" isRead>
                  {memberCount}
                </Badge>
              </span>
              <span className="awx-c-list-group">
                <Trans>Teams</Trans>
                <Badge className="awx-c-list-group--badge" isRead>
                  {teamCount}
                </Badge>
              </span>
            </DataListCell>
          ]}
          />
        </DataListItemRow>
      </DataListItem>
    );
  }
}
export default OrganizationListItem;
