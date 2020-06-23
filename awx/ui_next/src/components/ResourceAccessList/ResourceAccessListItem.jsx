import 'styled-components/macro';
import React from 'react';
import { func } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Chip,
  DataListItem,
  DataListItemRow,
  DataListItemCells as PFDataListItemCells,
  Text,
  TextContent,
  TextVariants,
} from '@patternfly/react-core';
import { Link } from 'react-router-dom';
import styled from 'styled-components';
import DataListCell from '../DataListCell';

import ChipGroup from '../ChipGroup';
import { DetailList, Detail } from '../DetailList';
import { AccessRecord } from '../../types';

const DataListItemCells = styled(PFDataListItemCells)`
  align-items: start;
`;

class ResourceAccessListItem extends React.Component {
  static propTypes = {
    accessRecord: AccessRecord.isRequired,
    onRoleDelete: func.isRequired,
  };

  constructor(props) {
    super(props);
    this.renderChip = this.renderChip.bind(this);
  }

  getRoleLists() {
    const { accessRecord } = this.props;
    const teamRoles = [];
    const userRoles = [];

    function sort(item) {
      const { role } = item;
      if (role.team_id) {
        teamRoles.push(role);
      } else {
        userRoles.push(role);
      }
    }

    accessRecord.summary_fields.direct_access.map(sort);
    accessRecord.summary_fields.indirect_access.map(sort);
    return [teamRoles, userRoles];
  }

  renderChip(role) {
    const { accessRecord, onRoleDelete } = this.props;
    return (
      <Chip
        key={role.id}
        onClick={() => {
          onRoleDelete(role, accessRecord);
        }}
        isReadOnly={!role.user_capabilities.unattach}
      >
        {role.name}
      </Chip>
    );
  }

  render() {
    const { accessRecord, i18n } = this.props;
    const [teamRoles, userRoles] = this.getRoleLists();

    return (
      <DataListItem
        aria-labelledby="access-list-item"
        key={accessRecord.id}
        id={`${accessRecord.id}`}
      >
        <DataListItemRow>
          <DataListItemCells
            dataListCells={[
              <DataListCell key="name">
                {accessRecord.username && (
                  <TextContent>
                    {accessRecord.id ? (
                      <Text component={TextVariants.h6}>
                        <Link
                          to={{ pathname: `/users/${accessRecord.id}/details` }}
                          css="font-weight: bold"
                        >
                          {accessRecord.username}
                        </Link>
                      </Text>
                    ) : (
                      <Text component={TextVariants.h6} css="font-weight: bold">
                        {accessRecord.username}
                      </Text>
                    )}
                  </TextContent>
                )}
                {accessRecord.first_name || accessRecord.last_name ? (
                  <DetailList stacked>
                    <Detail
                      label={i18n._(t`Name`)}
                      value={`${accessRecord.first_name} ${accessRecord.last_name}`}
                    />
                  </DetailList>
                ) : null}
              </DataListCell>,
              <DataListCell key="roles">
                <DetailList stacked>
                  {userRoles.length > 0 && (
                    <Detail
                      label={i18n._(t`User Roles`)}
                      value={
                        <ChipGroup numChips={5} totalChips={userRoles.length}>
                          {userRoles.map(this.renderChip)}
                        </ChipGroup>
                      }
                    />
                  )}
                  {teamRoles.length > 0 && (
                    <Detail
                      label={i18n._(t`Team Roles`)}
                      value={
                        <ChipGroup numChips={5} totalChips={teamRoles.length}>
                          {teamRoles.map(this.renderChip)}
                        </ChipGroup>
                      }
                    />
                  )}
                </DetailList>
              </DataListCell>,
            ]}
          />
        </DataListItemRow>
      </DataListItem>
    );
  }
}

export default withI18n()(ResourceAccessListItem);
