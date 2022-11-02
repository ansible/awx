import React from 'react';
import { Link } from 'react-router-dom';
import PropTypes from 'prop-types';
import { Button } from '@patternfly/react-core';
import { Tr, Td } from '@patternfly/react-table';
import { t } from '@lingui/macro';

import { PencilAltIcon } from '@patternfly/react-icons';
import { ActionsTd, ActionItem } from 'components/PaginatedTable';

function OrganizationTeamListItem({ team, detailUrl }) {
  return (
    <Tr id={`team-row-${team.id}`} ouiaId={`team-row-${team.id}`}>
      <Td dataLabel={t`Name`}>
        <Link to={`${detailUrl}/details`}>
          <b>{team.name}</b>
        </Link>
      </Td>
      <ActionsTd dataLabel={t`Actions`}>
        <ActionItem
          visible={team.summary_fields.user_capabilities.edit}
          tooltip={t`Edit Team`}
        >
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
        </ActionItem>
      </ActionsTd>
    </Tr>
  );
}

OrganizationTeamListItem.propTypes = {
  team: PropTypes.shape({ id: PropTypes.number, name: PropTypes.string })
    .isRequired,
  detailUrl: PropTypes.string.isRequired,
};

export default OrganizationTeamListItem;
