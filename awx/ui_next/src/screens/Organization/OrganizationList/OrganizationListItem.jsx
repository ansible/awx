import React from 'react';
import { string, bool, func } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Badge as PFBadge,
  Button,
  DataListAction as _DataListAction,
  DataListCheck,
  DataListItem,
  DataListItemCells,
  DataListItemRow,
  Tooltip,
} from '@patternfly/react-core';

import { Link } from 'react-router-dom';
import styled from 'styled-components';
import { PencilAltIcon } from '@patternfly/react-icons';
import DataListCell from '../../../components/DataListCell';

import { Organization } from '../../../types';

const Badge = styled(PFBadge)`
  margin-left: 8px;
`;

const ListGroup = styled.span`
  margin-left: 24px;

  &:first-of-type {
    margin-left: 0;
  }
`;

const DataListAction = styled(_DataListAction)`
  align-items: center;
  display: grid;
  grid-gap: 16px;
  grid-template-columns: 40px;
`;

function OrganizationListItem({
  organization,
  isSelected,
  onSelect,
  detailUrl,
  i18n,
}) {
  const labelId = `check-action-${organization.id}`;
  return (
    <DataListItem
      key={organization.id}
      aria-labelledby={labelId}
      id={`${organization.id}`}
    >
      <DataListItemRow>
        <DataListCheck
          id={`select-organization-${organization.id}`}
          checked={isSelected}
          onChange={onSelect}
          aria-labelledby={labelId}
        />
        <DataListItemCells
          dataListCells={[
            <DataListCell key="name" id={labelId}>
              <Link to={`${detailUrl}`}>
                <b>{organization.name}</b>
              </Link>
            </DataListCell>,
            <DataListCell key="related-field-counts">
              <ListGroup>
                {i18n._(t`Members`)}
                <Badge isRead>
                  {organization.summary_fields.related_field_counts.users}
                </Badge>
              </ListGroup>
              <ListGroup>
                {i18n._(t`Teams`)}
                <Badge isRead>
                  {organization.summary_fields.related_field_counts.teams}
                </Badge>
              </ListGroup>
            </DataListCell>,
          ]}
        />
        <DataListAction aria-label="actions" aria-labelledby={labelId}>
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
        </DataListAction>
      </DataListItemRow>
    </DataListItem>
  );
}

OrganizationListItem.propTypes = {
  organization: Organization.isRequired,
  detailUrl: string.isRequired,
  isSelected: bool.isRequired,
  onSelect: func.isRequired,
};

export default withI18n()(OrganizationListItem);
