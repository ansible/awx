import React, { Fragment } from 'react';
import { string, bool, func } from 'prop-types';
import { withI18n } from '@lingui/react';
import {
  DataListItem,
  DataListItemRow,
  DataListItemCells,
} from '@patternfly/react-core';
import { Link } from 'react-router-dom';

import DataListCell from '@components/DataListCell';
import DataListCheck from '@components/DataListCheck';
import VerticalSeparator from '@components/VerticalSeparator';
import { Team } from '@types';

class TeamListItem extends React.Component {
  static propTypes = {
    team: Team.isRequired,
    detailUrl: string.isRequired,
    isSelected: bool.isRequired,
    onSelect: func.isRequired,
  };

  render() {
    const { team, isSelected, onSelect, detailUrl } = this.props;
    const labelId = `check-action-${team.id}`;
    return (
      <DataListItem key={team.id} aria-labelledby={labelId}>
        <DataListItemRow>
          <DataListCheck
            id={`select-team-${team.id}`}
            checked={isSelected}
            onChange={onSelect}
            aria-labelledby={labelId}
          />
          <DataListItemCells
            dataListCells={[
              <DataListCell key="divider">
                <VerticalSeparator />
                <Link
                  id={labelId}
                  to={`${detailUrl}`}
                  style={{ marginRight: '10px' }}
                >
                  <b>{team.name}</b>
                </Link>
              </DataListCell>,
              <DataListCell key="organization">
                {team.summary_fields.organization && (
                  <Fragment>
                    <b style={{ marginRight: '20px' }}>Organization</b>
                    <Link
                      to={`/organizations/${team.summary_fields.organization.id}/details`}
                    >
                      <b>{team.summary_fields.organization.name}</b>
                    </Link>
                  </Fragment>
                )}
              </DataListCell>,
              <DataListCell lastcolumn="true" key="action">
                edit button goes here
              </DataListCell>,
            ]}
          />
        </DataListItemRow>
      </DataListItem>
    );
  }
}
export default withI18n()(TeamListItem);
