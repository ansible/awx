import React from 'react';
import { Link } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  DataListItemCells,
  DataListItemRow,
  DataListItem,
} from '@patternfly/react-core';
import DataListCell from '../../../components/DataListCell';

function UserTeamsListItem({ team, i18n }) {
  return (
    <DataListItem aria-labelledby={`team-${team.id}`}>
      <DataListItemRow>
        <DataListItemCells
          dataListCells={[
            <DataListCell key="name">
              <Link to={`/teams/${team.id}/details`} id={`team-${team.id}`}>
                {team.name}
              </Link>
            </DataListCell>,
            <DataListCell key="organization">
              {team.summary_fields.organization && (
                <>
                  <b css="margin-right: 24px">{i18n._(t`Organization`)}</b>
                  <Link
                    to={`/organizations/${team.summary_fields.organization.id}/details`}
                  >
                    <b>{team.summary_fields.organization.name}</b>
                  </Link>
                </>
              )}
            </DataListCell>,
            <DataListCell key="description">{team.description}</DataListCell>,
          ]}
        />
      </DataListItemRow>
    </DataListItem>
  );
}

export default withI18n()(UserTeamsListItem);
