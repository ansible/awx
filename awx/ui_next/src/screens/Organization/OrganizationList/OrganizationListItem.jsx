import React from 'react';
import { string, bool, func } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Badge as PFBadge,
  DataListItem,
  DataListItemRow,
  DataListItemCells,
  Tooltip,
} from '@patternfly/react-core';
import { Link } from 'react-router-dom';
import styled from 'styled-components';
import { PencilAltIcon } from '@patternfly/react-icons';

import ActionButtonCell from '@components/ActionButtonCell';
import DataListCell from '@components/DataListCell';
import DataListCheck from '@components/DataListCheck';
import ListActionButton from '@components/ListActionButton';
import VerticalSeparator from '@components/VerticalSeparator';
import { Organization } from '@types';

const Badge = styled(PFBadge)`
  align-items: center;
  display: flex;
  justify-content: center;
  margin-left: 10px;
`;

const ListGroup = styled.span`
  display: flex;
  margin-left: 40px;

  @media screen and (min-width: 768px) {
    margin-left: 20px;

    &:first-of-type {
      margin-left: 0;
    }
  }
`;

class OrganizationListItem extends React.Component {
  static propTypes = {
    organization: Organization.isRequired,
    detailUrl: string.isRequired,
    isSelected: bool.isRequired,
    onSelect: func.isRequired,
  };

  render() {
    const { organization, isSelected, onSelect, detailUrl, i18n } = this.props;
    const labelId = `check-action-${organization.id}`;
    return (
      <DataListItem key={organization.id} aria-labelledby={labelId}>
        <DataListItemRow>
          <DataListCheck
            id={`select-organization-${organization.id}`}
            checked={isSelected}
            onChange={onSelect}
            aria-labelledby={labelId}
          />
          <DataListItemCells
            dataListCells={[
              <DataListCell key="divider">
                <VerticalSeparator />
                <span id={labelId}>
                  <Link to={`${detailUrl}`}>
                    <b>{organization.name}</b>
                  </Link>
                </span>
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
              <ActionButtonCell lastcolumn="true" key="action">
                {organization.summary_fields.user_capabilities.edit && (
                  <Tooltip
                    content={i18n._(t`Edit Organization`)}
                    position="top"
                  >
                    <ListActionButton
                      variant="plain"
                      component={Link}
                      to={`/organizations/${organization.id}/edit`}
                    >
                      <PencilAltIcon />
                    </ListActionButton>
                  </Tooltip>
                )}
              </ActionButtonCell>,
            ]}
          />
        </DataListItemRow>
      </DataListItem>
    );
  }
}
export default withI18n()(OrganizationListItem);
