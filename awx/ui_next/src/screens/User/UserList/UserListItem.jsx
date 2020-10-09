import 'styled-components/macro';
import React, { Fragment } from 'react';
import { string, bool, func } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Button,
  DataListAction,
  DataListCheck,
  DataListItem,
  DataListItemCells,
  DataListItemRow,
  Label,
  Tooltip,
} from '@patternfly/react-core';

import { Link } from 'react-router-dom';
import { PencilAltIcon } from '@patternfly/react-icons';
import DataListCell from '../../../components/DataListCell';

import { User } from '../../../types';

function UserListItem({ user, isSelected, onSelect, detailUrl, i18n }) {
  const labelId = `check-action-${user.id}`;

  let user_type;
  if (user.is_superuser) {
    user_type = i18n._(t`System Administrator`);
  } else if (user.is_system_auditor) {
    user_type = i18n._(t`System Auditor`);
  } else {
    user_type = i18n._(t`Normal User`);
  }

  const ldapUser = user.ldap_dn;
  const socialAuthUser = user.auth.length > 0;

  return (
    <DataListItem key={user.id} aria-labelledby={labelId} id={`${user.id}`}>
      <DataListItemRow>
        <DataListCheck
          id={`select-user-${user.id}`}
          checked={isSelected}
          onChange={onSelect}
          aria-labelledby={labelId}
        />
        <DataListItemCells
          dataListCells={[
            <DataListCell key="username" aria-label={i18n._(t`username`)}>
              <span id={labelId}>
                <Link to={`${detailUrl}`} id={labelId}>
                  <b>{user.username}</b>
                </Link>
              </span>
              {ldapUser && (
                <span css="margin-left: 12px">
                  <Label aria-label={i18n._(t`ldap user`)}>
                    {i18n._(t`LDAP`)}
                  </Label>
                </span>
              )}
              {socialAuthUser && (
                <span css="margin-left: 12px">
                  <Label aria-label={i18n._(t`social login`)}>
                    {i18n._(t`SOCIAL`)}
                  </Label>
                </span>
              )}
            </DataListCell>,
            <DataListCell
              key="first-name"
              aria-label={i18n._(t`user first name`)}
            >
              {user.first_name && (
                <Fragment>
                  <b css="margin-right: 24px">{i18n._(t`First Name`)}</b>
                  {user.first_name}
                </Fragment>
              )}
            </DataListCell>,
            <DataListCell
              key="last-name"
              aria-label={i18n._(t`user last name`)}
            >
              {user.last_name && (
                <Fragment>
                  <b css="margin-right: 24px">{i18n._(t`Last Name`)}</b>
                  {user.last_name}
                </Fragment>
              )}
            </DataListCell>,
            <DataListCell key="user-type" aria-label={i18n._(t`user type`)}>
              {user_type}
            </DataListCell>,
          ]}
        />
        <DataListAction
          aria-label="actions"
          aria-labelledby={labelId}
          id={labelId}
        >
          {user.summary_fields.user_capabilities.edit && (
            <Tooltip content={i18n._(t`Edit User`)} position="top">
              <Button
                aria-label={i18n._(t`Edit User`)}
                variant="plain"
                component={Link}
                to={`/users/${user.id}/edit`}
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

UserListItem.prototype = {
  user: User.isRequired,
  detailUrl: string.isRequired,
  isSelected: bool.isRequired,
  onSelect: func.isRequired,
};

export default withI18n()(UserListItem);
