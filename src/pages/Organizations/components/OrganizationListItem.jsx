import React from 'react';
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
      <Checkbox
        checked={isSelected}
        onChange={onSelect}
        aria-label={`select organization ${itemId}`}
        id={`select-organization-${itemId}`}
      />
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
        Users
      </Link>
      <Badge isRead>
        {' '}
        {userCount}
        {' '}
      </Badge>
      <Link to={`${detailUrl}?tab=teams`}>
        Teams
      </Link>
      <Badge isRead>
        {' '}
        {teamCount}
        {' '}
      </Badge>
      <Link to={`${detailUrl}?tab=admins`}>
        Admins
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
