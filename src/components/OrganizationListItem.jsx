import React from 'react';
import {
  Badge,
  Checkbox,
} from '@patternfly/react-core';

export default ({ itemId, name, userCount, teamCount, adminCount, isSelected, onSelect }) => (
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
        <a href={`#/organizations/${itemId}`}>{ name }</a>
      </span>
    </div>
    <div className="pf-c-data-list__cell">
      <a href="#/dashboard"> Users </a>
      <Badge isRead>
        {' '}
        {userCount}
        {' '}
      </Badge>
      <a href="#/dashboard"> Teams </a>
      <Badge isRead>
        {' '}
        {teamCount}
        {' '}
      </Badge>
      <a href="#/dashboard"> Admins </a>
      <Badge isRead>
        {' '}
        {adminCount}
        {' '}
      </Badge>
    </div>
    <div className="pf-c-data-list__cell" />
  </li>
);
