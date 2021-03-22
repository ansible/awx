import React from 'react';
import { string, bool, func } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Button, Tooltip } from '@patternfly/react-core';
import { Tr, Td } from '@patternfly/react-table';
import { Link } from 'react-router-dom';
import styled from 'styled-components';
import {
  ExclamationTriangleIcon as PFExclamationTriangleIcon,
  PencilAltIcon,
} from '@patternfly/react-icons';
import { ActionsTd, ActionItem } from '../../../components/PaginatedTable';

import { Organization } from '../../../types';

const ExclamationTriangleIcon = styled(PFExclamationTriangleIcon)`
  color: var(--pf-global--warning-color--100);
  margin-left: 18px;
`;
function OrganizationListItem({
  organization,
  isSelected,
  onSelect,
  rowIndex,
  detailUrl,
  i18n,
}) {
  const labelId = `check-action-${organization.id}`;

  const missingExecutionEnvironment =
    organization.custom_virtualenv && !organization.default_environment;

  return (
    <Tr id={`org-row-${organization.id}`}>
      <Td
        select={{
          rowIndex,
          isSelected,
          onSelect,
          disable: false,
        }}
        dataLabel={i18n._(t`Selected`)}
      />
      <Td id={labelId} dataLabel={i18n._(t`Name`)}>
        <span>
          <Link to={`${detailUrl}`}>
            <b>{organization.name}</b>
          </Link>
        </span>
        {missingExecutionEnvironment && (
          <span>
            <Tooltip
              className="missing-execution-environment"
              content={i18n._(
                t`Custom virtual environment ${organization.custom_virtualenv} must be replaced by an execution environment.`
              )}
              position="right"
            >
              <ExclamationTriangleIcon />
            </Tooltip>
          </span>
        )}
      </Td>
      <Td dataLabel={i18n._(t`Members`)}>
        {organization.summary_fields.related_field_counts.users}
      </Td>
      <Td dataLabel={i18n._(t`Teams`)}>
        {organization.summary_fields.related_field_counts.teams}
      </Td>
      <ActionsTd dataLabel={i18n._(t`Actions`)}>
        <ActionItem
          visible={organization.summary_fields.user_capabilities.edit}
          tooltip={i18n._(t`Edit Organization`)}
        >
          <Button
            ouiaId={`${organization.id}-edit-button`}
            aria-label={i18n._(t`Edit Organization`)}
            variant="plain"
            component={Link}
            to={`/organizations/${organization.id}/edit`}
          >
            <PencilAltIcon />
          </Button>
        </ActionItem>
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
