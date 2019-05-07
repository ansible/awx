import React from 'react';
import { string, bool, func } from 'prop-types';
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
import { Organization } from '../../../types';

class OrganizationListItem extends React.Component {
  static propTypes = {
    organization: Organization.isRequired,
    detailUrl: string.isRequired,
    isSelected: bool.isRequired,
    onSelect: func.isRequired
  }

  render () {
    const {
      organization,
      isSelected,
      onSelect,
      detailUrl,
    } = this.props;
    const labelId = `check-action-${organization.id}`;
    return (
      <DataListItem key={organization.id} aria-labelledby={labelId}>
        <DataListItemRow>
          <DataListCheck
            id={`select-organization-${organization.id}`}
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
                  <b>{organization.name}</b>
                </Link>
              </span>
            </DataListCell>,
            <DataListCell key="org-members" width={2}>
              <span className="awx-c-list-group">
                <Trans>Members</Trans>
                <Badge className="awx-c-list-group--badge" isRead>
                  {organization.summary_fields.related_field_counts.users}
                </Badge>
              </span>
              <span className="awx-c-list-group">
                <Trans>Teams</Trans>
                <Badge className="awx-c-list-group--badge" isRead>
                  {organization.summary_fields.related_field_counts.teams}
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
