import React from 'react';
import { Link } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  DataListItemCells,
  DataListItemRow,
  DataListItem,
} from '@patternfly/react-core';
import DataListCell from '@components/DataListCell';

function UserOrganizationListItem({ organization, i18n }) {
  return (
    <DataListItem aria-labelledby={i18n._(t`User Organization List Item`)}>
      <DataListItemRow>
        <DataListItemCells
          dataListCells={[
            <DataListCell key={organization.id}>
              <Link to={`/organizations/${organization.id}/details`}>
                {organization.name}
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

export default withI18n()(UserOrganizationListItem);
