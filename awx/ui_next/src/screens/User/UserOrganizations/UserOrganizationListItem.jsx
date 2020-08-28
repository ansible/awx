import React from 'react';
import { Link } from 'react-router-dom';
import {
  DataListItemCells,
  DataListItemRow,
  DataListItem,
} from '@patternfly/react-core';
import DataListCell from '../../../components/DataListCell';

export default function UserOrganizationListItem({ organization }) {
  const labelId = `organization-${organization.id}`;
  return (
    <DataListItem aria-labelledby={labelId}>
      <DataListItemRow>
        <DataListItemCells
          dataListCells={[
            <DataListCell key={organization.id}>
              <Link
                to={`/organizations/${organization.id}/details`}
                id={labelId}
              >
                <b>{organization.name}</b>
              </Link>
            </DataListCell>,
            <DataListCell key={organization.description}>
              {organization.description}
            </DataListCell>,
          ]}
        />
      </DataListItemRow>
    </DataListItem>
  );
}
