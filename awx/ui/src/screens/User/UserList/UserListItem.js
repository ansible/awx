import React from 'react';
import 'styled-components/macro';
import { string, bool, func } from 'prop-types';

import { t } from '@lingui/macro';
import { Button, Label } from '@patternfly/react-core';
import { Tr } from '@patternfly/react-table';
import { Link } from 'react-router-dom';
import { PencilAltIcon } from '@patternfly/react-icons';
import { ActionsTd, ActionItem, TableDatum } from 'components/PaginatedTable';

import { User } from 'types';

function UserListItem({ user, isSelected, onSelect, detailUrl, rowIndex }) {
  const labelId = `check-action-${user.id}`;

  let user_type;
  if (user.is_superuser) {
    user_type = t`System Administrator`;
  } else if (user.is_system_auditor) {
    user_type = t`System Auditor`;
  } else {
    user_type = t`Normal User`;
  }

  const ldapUser = user.ldap_dn;
  const socialAuthUser = user.auth.length > 0;

  return (
    <Tr id={`user-row-${user.id}`} ouiaId={`user-row-${user.id}`}>
      <TableDatum
        select={{
          rowIndex,
          isSelected,
          onSelect,
        }}
      />
      <TableDatum
        value={
          <>
            <Link to={`${detailUrl}`}>
              <b>{user.username}</b>
            </Link>
            {ldapUser && (
              <span css="margin-left: 12px">
                <Label aria-label={t`ldap user`}>{t`LDAP`}</Label>
              </span>
            )}
            {socialAuthUser && (
              <span css="margin-left: 12px">
                <Label aria-label={t`social login`}>{t`SOCIAL`}</Label>
              </span>
            )}
          </>
        }
        detailUrl={detailUrl}
        id={labelId}
        dataLabel={t`Username`}
      />

      <TableDatum value={user.first_name} dataLabel={t`First Name`} />
      <TableDatum dataLabel={t`Last Name`} value={user.last_name} />
      <TableDatum dataLabel={t`Role`} value={user_type} />
      <ActionsTd dataLabel={t`Actions`}>
        <ActionItem
          visible={user.summary_fields.user_capabilities.edit}
          tooltip={t`Edit User`}
        >
          <Button
            ouiaId={`${user.id}-edit-button`}
            aria-label={t`Edit User`}
            variant="plain"
            component={Link}
            to={`/users/${user.id}/edit`}
          >
            <PencilAltIcon />
          </Button>
        </ActionItem>
      </ActionsTd>
    </Tr>
  );
}

UserListItem.prototype = {
  user: User.isRequired,
  detailUrl: string.isRequired,
  isSelected: bool.isRequired,
  onSelect: func.isRequired,
};

export default UserListItem;
