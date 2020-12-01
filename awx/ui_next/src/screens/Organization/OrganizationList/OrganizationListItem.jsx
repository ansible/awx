import React from 'react';
import { string, bool, func } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Button, Tooltip } from '@patternfly/react-core';
import { Tr, Td } from '@patternfly/react-table';
import { Link } from 'react-router-dom';
import { PencilAltIcon } from '@patternfly/react-icons';
import { ActionsTd } from '../../../components/PaginatedTable';

import { Organization } from '../../../types';

function OrganizationListItem({
  organization,
  isSelected,
  onSelect,
  rowIndex,
  detailUrl,
  i18n,
}) {
  const labelId = `check-action-${organization.id}`;
  return (
    <Tr id={`${organization.id}`}>
      <Td
        select={{
          rowIndex,
          isSelected,
          onSelect,
          disable: false,
        }}
      />
      <Td id={labelId}>
        <Link to={`${detailUrl}`}>
          <b>{organization.name}</b>
        </Link>
      </Td>
      <Td>{organization.summary_fields.related_field_counts.users}</Td>
      <Td>{organization.summary_fields.related_field_counts.teams}</Td>
      <ActionsTd numActions={1}>
        {organization.summary_fields.user_capabilities.edit ? (
          <Tooltip content={i18n._(t`Edit Organization`)} position="top">
            <Button
              aria-label={i18n._(t`Edit Organization`)}
              variant="plain"
              component={Link}
              to={`/organizations/${organization.id}/edit`}
            >
              <PencilAltIcon />
            </Button>
          </Tooltip>
        ) : (
          ''
        )}
      </ActionsTd>
    </Tr>
  );
}

OrganizationListItem.propTypes = {
  organization: Organization.isRequired,
  detailUrl: string.isRequired,
  isSelected: bool.isRequired,
  onSelect: func.isRequired,
};

export default withI18n()(OrganizationListItem);
