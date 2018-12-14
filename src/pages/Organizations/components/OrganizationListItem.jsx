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

export default ({
  itemId,
  name,
  userCount,
  teamCount,
  adminCount,
  isSelected,
  onSelect,
  detailUrl,
  parentBreadcrumb
}) => (
  <li key={itemId} className="pf-c-data-list__item" aria-labelledby="check-action-item1">
    <div className="pf-c-data-list__check">
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
    </div>
    <div className="pf-c-data-list__cell">
      <span id="check-action-item1">
        <Link
          to={{
            pathname: detailUrl,
            state: { breadcrumb: [parentBreadcrumb, { name, url: detailUrl }] }
          }}
        >
          {name}
        </Link>
      </span>
    </div>
    <div className="pf-c-data-list__cell">
      <Link to={`${detailUrl}?tab=users`}>
        <Trans>Users</Trans>
      </Link>
      <Badge isRead>
        {' '}
        {userCount}
        {' '}
      </Badge>
      <Link to={`${detailUrl}?tab=teams`}>
        <Trans>Teams</Trans>
      </Link>
      <Badge isRead>
        {' '}
        {teamCount}
        {' '}
      </Badge>
      <Link to={`${detailUrl}?tab=admins`}>
        <Trans>Admins</Trans>
      </Link>
      <Badge isRead>
        {' '}
        {adminCount}
        {' '}
      </Badge>
    </div>
    <div className="pf-c-data-list__cell" />
  </li>
);
