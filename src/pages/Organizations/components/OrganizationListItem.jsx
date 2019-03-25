import React from 'react';
import { I18n } from '@lingui/react';
import { Trans, t } from '@lingui/macro';
import {
  Badge,
  Checkbox,
  Button,
} from '@patternfly/react-core';
import {
  TrashAltIcon,
} from '@patternfly/react-icons';
import {
  Link
} from 'react-router-dom';

import VerticalSeparator from '../../../components/VerticalSeparator';

class OrganizationListItem extends React.Component {
  render () {
    const {
      itemId,
      name,
      userCount,
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
          <Link to={`${detailUrl}/access`}>
            <Trans>Users</Trans>
          </Link>
          <Badge isRead>
            {' '}
            {userCount}
            {' '}
          </Badge>
          <Link to={`${detailUrl}/teams`}>
            <Trans>Teams</Trans>
          </Link>
          <Badge isRead>
            {' '}
            {teamCount}
            {' '}
          </Badge>
        </div>
        <div className="pf-c-data-list__cell" />
      </li>
    );
  }
}
export default OrganizationListItem;

