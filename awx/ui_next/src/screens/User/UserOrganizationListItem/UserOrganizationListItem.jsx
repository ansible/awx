import React from 'react';
import { Link } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  DataList,
  DataListItemCells,
  DataListItemRow,
  DataListItem,
  DataListCell,
} from '@patternfly/react-core';

function UserOrganizationListItem({ organization, i18n }) {
  return (
    <DataList aria-label={i18n._(t`User Organization List Item`)}>
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
    </DataList>
  );
}

export default withI18n()(UserOrganizationListItem);
