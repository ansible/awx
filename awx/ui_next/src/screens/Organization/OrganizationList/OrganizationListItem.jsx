import React from 'react';
import { string, bool, func } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Badge as PFBadge,
  DataListItem,
  DataListItemRow,
  DataListItemCells,
} from '@patternfly/react-core';
import { Link } from 'react-router-dom';
import styled from 'styled-components';

import DataListCell from '@components/DataListCell';
import DataListCheck from '@components/DataListCheck';
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
              <DataListCell
                key="related-field-counts"
                righthalf="true"
                width={2}
              >
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
        </DataListItemRow>
      </DataListItem>
    );
  }
}
export default withI18n()(OrganizationListItem);
