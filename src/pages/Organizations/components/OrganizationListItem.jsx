import React from 'react';
import { I18n } from '@lingui/react';
import { Trans, t } from '@lingui/macro';
import {
  Badge,
  Checkbox,
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
    return (
      <li key={itemId} className="pf-c-data-list__item" aria-labelledby="check-action-item1">
        <I18n>
          {({ i18n }) => (
            <Checkbox
              checked={isSelected}
              onChange={onSelect}
              aria-label={i18n._(t`select organization ${itemId}`)}
              id={`select-organization-${itemId}`}
            />
          )}
        </I18n>
        <VerticalSeparator />
        <div className="pf-c-data-list__cell">
          <span id="check-action-item1">
            <Link
              to={`${detailUrl}`}
            >
              <b>{name}</b>
            </Link>
          </span>
        </div>
        <div className="pf-c-data-list__cell">
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
        </div>
        <div className="pf-c-data-list__cell" />
      </li>
    );
  }
}
export default OrganizationListItem;
