import React from 'react';
import { func } from 'prop-types';
import { I18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  DataListItem,
  DataListCell,
  Text,
  TextContent,
  TextVariants,
  Chip,
} from '@patternfly/react-core';
import { Link } from 'react-router-dom';
import { AccessRecord } from '../../../types';
import BasicChip from '../../../components/BasicChip/BasicChip';

const userRolesWrapperStyle = {
  display: 'flex',
  flexWrap: 'wrap',
};

const detailWrapperStyle = {
  display: 'grid',
  gridTemplateColumns: 'minmax(70px, max-content) minmax(60px, max-content)',
};

const detailLabelStyle = {
  fontWeight: '700',
  lineHeight: '24px',
  marginRight: '20px',
};

const detailValueStyle = {
  lineHeight: '28px',
  overflow: 'visible',
};

/* TODO: does PF offer any sort of <dl> treatment for this? */
const Detail = ({ label, value, url, customStyles }) => {
  let detail = null;
  if (value) {
    detail = (
      <TextContent style={{ ...detailWrapperStyle, ...customStyles }}>
        {url ? (
          <Link to={{ pathname: url }}>
            <Text component={TextVariants.h6} style={detailLabelStyle}>{label}</Text>
          </Link>) : (<Text component={TextVariants.h6} style={detailLabelStyle}>{label}</Text>
        )}
        <Text component={TextVariants.p} style={detailValueStyle}>{value}</Text>
      </TextContent>
    );
  }
  return detail;
};

class OrganizationAccessItem extends React.Component {
  static propTypes = {
    accessRecord: AccessRecord.isRequired,
    onRoleDelete: func.isRequired,
  };

  getRoleLists () {
    const { accessRecord } = this.props;
    const teamRoles = [];
    const userRoles = [];

    function sort (item) {
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

  render () {
    const { accessRecord, onRoleDelete } = this.props;
    const [teamRoles, userRoles] = this.getRoleLists();

    return (
      <I18n>
        {({ i18n }) => (
          <DataListItem aria-labelledby="access-list-item" key={accessRecord.id}>
            <DataListCell>
              {accessRecord.username && (
                <TextContent style={detailWrapperStyle}>
                  {accessRecord.url ? (
                    <Link to={{ pathname: accessRecord.url }}>
                      <Text component={TextVariants.h6} style={detailLabelStyle}>
                        {accessRecord.username}
                      </Text>
                    </Link>
                  ) : (
                    <Text component={TextVariants.h6} style={detailLabelStyle}>
                      {accessRecord.username}
                    </Text>
                  )}
                </TextContent>
              )}
              {accessRecord.first_name || accessRecord.last_name ? (
                <Detail
                  label={i18n._(t`Name`)}
                  value={`${accessRecord.first_name} ${accessRecord.last_name}`}
                  url={null}
                  customStyles={null}
                />
              ) : (
                null
              )}
            </DataListCell>
            <DataListCell>
              {userRoles.length > 0 && (
                <ul style={userRolesWrapperStyle}>
                  <Text component={TextVariants.h6} style={detailLabelStyle}>
                    {i18n._(t`User Roles`)}
                  </Text>
                  {userRoles.map(role => (
                    role.user_capabilities.unattach ? (
                      <Chip
                        key={role.id}
                        className="awx-c-chip"
                        onClick={() => { onRoleDelete(role, accessRecord); }}
                      >
                        {role.name}
                      </Chip>
                    ) : (
                      <BasicChip key={role.id}>
                        {role.name}
                      </BasicChip>
                    )
                  ))}
                </ul>
              )}
              {teamRoles.length > 0 && (
                <ul style={userRolesWrapperStyle}>
                  <Text component={TextVariants.h6} style={detailLabelStyle}>
                    {i18n._(t`Team Roles`)}
                  </Text>
                  {teamRoles.map(role => (
                    role.user_capabilities.unattach ? (
                      <Chip
                        key={role.id}
                        className="awx-c-chip"
                        onClick={() => { onRoleDelete(role, accessRecord); }}
                      >
                        {role.name}
                      </Chip>
                    ) : (
                      <BasicChip key={role.id}>
                        {role.name}
                      </BasicChip>
                    )
                  ))}
                </ul>
              )}
            </DataListCell>
          </DataListItem>
        )}
      </I18n>
    );
  }
}

export default OrganizationAccessItem;
