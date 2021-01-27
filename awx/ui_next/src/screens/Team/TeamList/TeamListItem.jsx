import 'styled-components/macro';
import React, { Fragment } from 'react';
import { string, bool, func } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Button } from '@patternfly/react-core';
import { Tr, Td } from '@patternfly/react-table';
import { Link } from 'react-router-dom';
import { PencilAltIcon } from '@patternfly/react-icons';
import { ActionsTd, ActionItem } from '../../../components/PaginatedTable';
import { Team } from '../../../types';

function TeamListItem({
  team,
  isSelected,
  onSelect,
  detailUrl,
  rowIndex,
  i18n,
}) {
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
        dataLabel={i18n._(t`Selected`)}
      />
      <Td id={labelId} dataLabel={i18n._(t`Name`)}>
        <Link id={labelId} to={`${detailUrl}`}>
          <b>{team.name}</b>
        </Link>
      </Td>
      <Td dataLabel={i18n._(t`Organization`)}>
        {team.summary_fields.organization && (
          <Link
            to={`/organizations/${team.summary_fields.organization.id}/details`}
          >
            <b>{team.summary_fields.organization.name}</b>
          </Link>
        )}
      </Td>
      <ActionsTd dataLabel={i18n._(t`Actions`)}>
        <ActionItem
          visible={team.summary_fields.user_capabilities.edit}
          tooltip={i18n._(t`Edit Team`)}
        >
          <Button
            aria-label={i18n._(t`Edit Team`)}
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
export default withI18n()(TeamListItem);
