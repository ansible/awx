import 'styled-components/macro';
import React, { Fragment } from 'react';
import { string, bool, func } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Button, Label } from '@patternfly/react-core';
import { Tr, Td } from '@patternfly/react-table';
import { Link } from 'react-router-dom';
import { PencilAltIcon } from '@patternfly/react-icons';
import { ActionsTd, ActionItem } from '../../../components/PaginatedTable';

import { User } from '../../../types';

function UserListItem({
  user,
  isSelected,
  onSelect,
  detailUrl,
  rowIndex,
  i18n,
}) {
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
    <Tr id={`user-row-${user.id}`}>
      <Td
        select={{
          rowIndex,
          isSelected,
          onSelect,
        }}
      />
      <Td id={labelId} dataLabel={i18n._(t`Username`)}>
        <Link to={`${detailUrl}`} id={labelId}>
          <b>{user.username}</b>
        </Link>
        {ldapUser && (
          <span css="margin-left: 12px">
            <Label aria-label={i18n._(t`ldap user`)}>{i18n._(t`LDAP`)}</Label>
          </span>
        )}
        {socialAuthUser && (
          <span css="margin-left: 12px">
            <Label aria-label={i18n._(t`social login`)}>
              {i18n._(t`SOCIAL`)}
            </Label>
          </span>
        )}
      </Td>
      <Td dataLabel={i18n._(t`First Name`)}>
        {user.first_name && (
          <Fragment>
            <b css="margin-right: 24px">{i18n._(t`First Name`)}</b>
            {user.first_name}
          </Fragment>
        )}
      </Td>
      <Td dataLabel={i18n._(t`Last Name`)}>
        {user.last_name && (
          <Fragment>
            <b css="margin-right: 24px">{i18n._(t`Last Name`)}</b>
            {user.last_name}
          </Fragment>
        )}
      </Td>
      <Td dataLabel={i18n._(t`Role`)}>{user_type}</Td>
      <ActionsTd dataLabel={i18n._(t`Actions`)}>
        <ActionItem
          visible={user.summary_fields.user_capabilities.edit}
          tooltip={i18n._(t`Edit User`)}
        >
          <Button
            aria-label={i18n._(t`Edit User`)}
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

export default withI18n()(UserListItem);
