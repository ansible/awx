import React from 'react';
import { bool, func } from 'prop-types';
import { Link } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  DataListItemCells,
  DataListItemRow,
  DataListItem,
  DataListCheck,
  Split,
  SplitItem,
} from '@patternfly/react-core';
import DataListCell from '../../../components/DataListCell';
import { Team } from '../../../types';

function UserTeamListItem({ team, isSelected, onSelect, i18n }) {
  return (
    <DataListItem
      key={team.id}
      id={`${team.id}`}
      aria-labelledby={`team-${team.id}`}
    >
      <DataListItemRow>
        <DataListCheck
          aria-labelledby={`team-${team.id}`}
          checked={isSelected}
          id={`team-${team.id}`}
          onChange={onSelect}
        />
        <DataListItemCells
          dataListCells={[
            <DataListCell key="name">
              <Link to={`/teams/${team.id}/details`} id={`team-${team.id}`}>
                {team.name}
              </Link>
            </DataListCell>,
            <DataListCell key="organization">
              {team.summary_fields.organization && (
                <Split hasGutter>
                  <SplitItem>
                    <b>{i18n._(t`Organization`)}</b>{' '}
                  </SplitItem>
                  <SplitItem>
                    <Link
                      to={`/organizations/${team.summary_fields.organization.id}/details`}
                    >
                      <b>{team.summary_fields.organization.name}</b>
                    </Link>
                  </SplitItem>
                </Split>
              )}
            </DataListCell>,
            <DataListCell key="description">{team.description}</DataListCell>,
          ]}
        />
      </DataListItemRow>
    </DataListItem>
  );
}

UserTeamListItem.prototype = {
  team: Team.isRequired,
  isSelected: bool.isRequired,
  onSelect: func.isRequired,
};

export default withI18n()(UserTeamListItem);
