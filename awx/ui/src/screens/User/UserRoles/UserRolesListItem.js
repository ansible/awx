import React from 'react';
import { t } from '@lingui/macro';
import { Chip } from '@patternfly/react-core';
import { Tr, Td } from '@patternfly/react-table';
import { Link } from 'react-router-dom';

function UserRolesListItem({ role, detailUrl, onSelect }) {
  const labelId = `userRole-${role.id}`;

  return (
    <Tr id={`user-role-row-${role.id}`} ouiaId={`user-role-row-${role.id}`}>
      <Td id={labelId} dataLabel={t`Name`}>
        {role.summary_fields.resource_name ? (
          <Link to={`${detailUrl}`} id={labelId}>
            <b>{role.summary_fields.resource_name}</b>
          </Link>
        ) : (
          <b>{t`System`}</b>
        )}
      </Td>
      <Td dataLabel={t`Type`}>
        {role.summary_fields
          ? role.summary_fields.resource_type_display_name
          : null}
      </Td>
      <Td dataLabel={t`Role`}>
        {role.name ? (
          <Chip
            key={role.name}
            aria-label={role.name}
            onClick={() => onSelect(role)}
            isReadOnly={!role.summary_fields.user_capabilities.unattach}
          >
            {role.name}
          </Chip>
        ) : null}
      </Td>
    </Tr>
  );
}

export default UserRolesListItem;
