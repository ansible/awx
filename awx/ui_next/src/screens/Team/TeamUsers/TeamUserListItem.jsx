import 'styled-components/macro';
import React from 'react';
import { string, func } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  DataListItem,
  DataListItemCells,
  DataListItemRow,
  Label as PFLabel,
} from '@patternfly/react-core';
import { Link } from 'react-router-dom';
import styled from 'styled-components';
import DataListCell from '../../../components/DataListCell';

import { User } from '../../../types';

function TeamUserListItem({ user, disassociateRole, detailUrl, i18n }) {
  const labelId = `check-action-${user.id}`;
  const Label = styled.b`
    margin-right: 20px;
  `;
  const hasDirectRoles = user.summary_fields.direct_access.length > 0;
  const hasIndirectRoles = user.summary_fields.indirect_access.length > 0;
  return (
    <DataListItem key={user.id} aria-labelledby={labelId} id={`${user.id}`}>
      <DataListItemRow>
        <DataListItemCells
          dataListCells={[
            <DataListCell aria-label={i18n._(t`username`)} key="username">
              <Link id={labelId} to={`${detailUrl}`}>
                <b>{user.username}</b>
              </Link>
            </DataListCell>,
            <DataListCell aria-label={i18n._(t`first name`)} key="first name">
              {user.first_name && (
                <>
                  <Label>{i18n._(t`First`)}</Label>
                  <span>{user.first_name}</span>
                </>
              )}
            </DataListCell>,
            <DataListCell aria-label={i18n._(t`last name`)} key="last name">
              {user.last_name && (
                <>
                  <Label>{i18n._(t`Last`)}</Label>
                  <span>{user.last}</span>
                </>
              )}
            </DataListCell>,
            <DataListCell aria-label={i18n._(t`roles`)} key="role">
              {hasDirectRoles && (
                <>
                  <Label>{i18n._(t`Roles`)}</Label>
                  <span>
                    {user.summary_fields.direct_access.map(role =>
                      role.role.name !== 'Read' ? (
                        <PFLabel
                          aria-label={role.role.name}
                          key={role.role.id}
                          role={role.role}
                          onClose={() => disassociateRole(role.role)}
                        >
                          {role.role.name}
                        </PFLabel>
                      ) : null
                    )}
                  </span>
                </>
              )}
            </DataListCell>,
            <DataListCell
              aria-label={i18n._(t`indirect role`)}
              key="indirectRole"
            >
              {hasIndirectRoles && (
                <>
                  <Label>{i18n._(t`Indirect Roles`)}</Label>
                  <span>
                    {user.summary_fields.indirect_access.map(role => (
                      <PFLabel key={role.role.id} credential={role.role}>
                        {role.role.name}
                      </PFLabel>
                    ))}
                  </span>
                </>
              )}
            </DataListCell>,
          ]}
        />
      </DataListItemRow>
    </DataListItem>
  );
}

TeamUserListItem.propTypes = {
  user: User.isRequired,
  detailUrl: string.isRequired,
  disassociateRole: func.isRequired,
};

export default withI18n()(TeamUserListItem);
