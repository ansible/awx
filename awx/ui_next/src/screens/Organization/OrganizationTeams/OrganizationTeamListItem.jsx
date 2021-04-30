import React from 'react';
import { Link } from 'react-router-dom';
import PropTypes from 'prop-types';
import {
  Button,
  DataListAction,
  DataListItem,
  DataListItemRow,
  DataListItemCells,
  Tooltip,
} from '@patternfly/react-core';
import { t } from '@lingui/macro';

import { PencilAltIcon } from '@patternfly/react-icons';
import DataListCell from '../../../components/DataListCell';

function OrganizationTeamListItem({ team, detailUrl }) {
  const labelId = `check-action-${team.id}`;

  return (
    <DataListItem aria-labelledby={labelId} id={`${team.id}`}>
      <DataListItemRow>
        <DataListItemCells
          dataListCells={[
            <DataListCell key="divider">
              <span>
                <Link to={`${detailUrl}/details`}>
                  <b aria-label={t`team name`}>{team.name}</b>
                </Link>
              </span>
            </DataListCell>,
          ]}
        />
        <DataListAction
          aria-label={t`actions`}
          aria-labelledby={labelId}
          id={labelId}
        >
          {team.summary_fields.user_capabilities.edit && (
            <Tooltip content={t`Edit Team`} position="top">
              <Button
                ouiaId={`${team.id}-edit-button`}
                aria-label={t`Edit Team`}
                css="grid-column: 2"
                variant="plain"
                component={Link}
                to={`${detailUrl}/edit`}
              >
                <PencilAltIcon />
              </Button>
            </Tooltip>
          )}
        </DataListAction>
      </DataListItemRow>
    </DataListItem>
  );
}

OrganizationTeamListItem.propTypes = {
  team: PropTypes.shape({ id: PropTypes.number, name: PropTypes.string })
    .isRequired,
  detailUrl: PropTypes.string.isRequired,
};

export default OrganizationTeamListItem;
