import 'styled-components/macro';
import React from 'react';
import { func } from 'prop-types';
import { t } from '@lingui/macro';
import { Chip } from '@patternfly/react-core';
import { Tr, Td } from '@patternfly/react-table';
import { Link } from 'react-router-dom';

import { AccessRecord } from 'types';
import ChipGroup from '../ChipGroup';
import { DetailList, Detail } from '../DetailList';

function ResourceAccessListItem({ accessRecord, onRoleDelete }) {
  ResourceAccessListItem.propTypes = {
    accessRecord: AccessRecord.isRequired,
    onRoleDelete: func.isRequired,
  };

  const getRoleLists = () => {
    const teamRoles = [];
    const userRoles = [];

    function sort(item) {
      const { role } = item;
      if (role.team_id) {
        teamRoles.push(role);
      } else {
        userRoles.push(role);
      }
    }

    accessRecord.summary_fields.direct_access.map(sort);
    accessRecord.summary_fields.indirect_access.map(sort);
    return [teamRoles, userRoles];
  };

  const renderChip = (role) => (
    <Chip
      key={role.id}
      onClick={() => {
        onRoleDelete(role, accessRecord);
      }}
      isReadOnly={!role.user_capabilities.unattach}
      ouiaId={`${role.name}-${role.id}`}
      closeBtnAriaLabel={t`Remove ${role.name} chip`}
    >
      {role.name}
    </Chip>
  );

  const [teamRoles, userRoles] = getRoleLists();

  return (
    <Tr
      id={`access-item-row-${accessRecord.id}`}
      ouiaId={`access-item-row-${accessRecord.id}`}
    >
      <Td id={`access-record-${accessRecord.id}`} dataLabel={t`Name`}>
        {accessRecord.id ? (
          <Link to={{ pathname: `/users/${accessRecord.id}/details` }}>
            <b>{accessRecord.username}</b>
          </Link>
        ) : (
          <b>{accessRecord.username}</b>
        )}
      </Td>
      <Td dataLabel={t`First name`}>{accessRecord.first_name}</Td>
      <Td dataLabel={t`Last name`}>{accessRecord.last_name}</Td>
      <Td dataLabel={t`Roles`}>
        <DetailList stacked>
          <Detail
            label={t`User Roles`}
            value={
              <ChipGroup
                numChips={5}
                totalChips={userRoles.length}
                ouiaId="user-role-chips"
              >
                {userRoles.map(renderChip)}
              </ChipGroup>
            }
            isEmpty={userRoles.length === 0}
          />
          <Detail
            label={t`Team Roles`}
            value={
              <ChipGroup
                numChips={5}
                totalChips={teamRoles.length}
                ouiaId="team-role-chips"
              >
                {teamRoles.map(renderChip)}
              </ChipGroup>
            }
            isEmpty={teamRoles.length === 0}
          />
        </DetailList>
      </Td>
    </Tr>
  );
}

export default ResourceAccessListItem;
