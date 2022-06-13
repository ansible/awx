import React from 'react';
import { Link } from 'react-router-dom';
import { t } from '@lingui/macro';
import { Tr, Td } from '@patternfly/react-table';

export default function UserOrganizationListItem({ organization }) {
  const labelId = `organization-${organization.id}`;
  return (
    <Tr
      id={`user-org-row-${organization.id}`}
      ouiaId={`user-org-row-${organization.id}`}
    >
      <Td id={labelId} dataLabel={t`Name`}>
        <Link to={`/organizations/${organization.id}/details`} id={labelId}>
          <b>{organization.name}</b>
        </Link>
      </Td>
      <Td dataLabel={t`Description`}>{organization.description}</Td>
    </Tr>
  );
}
