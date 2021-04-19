import 'styled-components/macro';
import React from 'react';
import { string, bool, func } from 'prop-types';

import { t } from '@lingui/macro';
import { Button } from '@patternfly/react-core';
import { Tr, Td } from '@patternfly/react-table';
import { Link } from 'react-router-dom';
import { PencilAltIcon } from '@patternfly/react-icons';
import { ActionsTd, ActionItem } from '../../../components/PaginatedTable';
import { Team } from '../../../types';

function TeamListItem({ team, isSelected, onSelect, detailUrl, rowIndex }) {
  TeamListItem.propTypes = {
    team: Team.isRequired,
    detailUrl: string.isRequired,
    isSelected: bool.isRequired,
    onSelect: func.isRequired,
  };

  const labelId = `check-action-${team.id}`;

  return (
    <Tr id={`team-row-${team.id}`}>
      <Td
        select={{
          rowIndex,
          isSelected,
          onSelect,
        }}
        dataLabel={t`Selected`}
      />
      <Td id={labelId} dataLabel={t`Name`}>
        <Link id={labelId} to={`${detailUrl}`}>
          <b>{team.name}</b>
        </Link>
      </Td>
      <Td dataLabel={t`Organization`}>
        {team.summary_fields.organization && (
          <Link
            to={`/organizations/${team.summary_fields.organization.id}/details`}
          >
            <b>{team.summary_fields.organization.name}</b>
          </Link>
        )}
      </Td>
      <ActionsTd dataLabel={t`Actions`}>
        <ActionItem
          visible={team.summary_fields.user_capabilities.edit}
          tooltip={t`Edit Team`}
        >
          <Button
            ouiaId={`${team.id}-edit-button`}
            aria-label={t`Edit Team`}
            variant="plain"
            component={Link}
            to={`/teams/${team.id}/edit`}
          >
            <PencilAltIcon />
          </Button>
        </ActionItem>
      </ActionsTd>
    </Tr>
  );
}
export default TeamListItem;
