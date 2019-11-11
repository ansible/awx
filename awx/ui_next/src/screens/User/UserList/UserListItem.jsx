import React, { Fragment } from 'react';
import { string, bool, func } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  DataListItem,
  DataListItemRow,
  DataListItemCells,
  Tooltip,
} from '@patternfly/react-core';
import { Link } from 'react-router-dom';
import { PencilAltIcon } from '@patternfly/react-icons';

import ActionButtonCell from '@components/ActionButtonCell';
import DataListCell from '@components/DataListCell';
import DataListCheck from '@components/DataListCheck';
import ListActionButton from '@components/ListActionButton';
import VerticalSeparator from '@components/VerticalSeparator';
import { User } from '@types';

class UserListItem extends React.Component {
  static propTypes = {
    user: User.isRequired,
    detailUrl: string.isRequired,
    isSelected: bool.isRequired,
    onSelect: func.isRequired,
  };

  render() {
    const { user, isSelected, onSelect, detailUrl, i18n } = this.props;
    const labelId = `check-action-${user.id}`;
    return (
      <DataListItem key={user.id} aria-labelledby={labelId}>
        <DataListItemRow>
          <DataListCheck
            id={`select-user-${user.id}`}
            checked={isSelected}
            onChange={onSelect}
            aria-labelledby={labelId}
          />
          <DataListItemCells
            dataListCells={[
              <DataListCell key="divider">
                <VerticalSeparator />
                <Link to={`${detailUrl}`} id={labelId}>
                  <b>{user.username}</b>
                </Link>
              </DataListCell>,
              <DataListCell key="first-name">
                {user.first_name && (
                  <Fragment>
                    <b css={{ marginRight: '20px' }}>{i18n._(t`First Name`)}</b>
                    {user.first_name}
                  </Fragment>
                )}
              </DataListCell>,
              <DataListCell key="last-name">
                {user.last_name && (
                  <Fragment>
                    <b css={{ marginRight: '20px' }}>{i18n._(t`Last Name`)}</b>
                    {user.last_name}
                  </Fragment>
                )}
              </DataListCell>,
              <ActionButtonCell lastcolumn="true" key="action">
                {user.summary_fields.user_capabilities.edit && (
                  <Tooltip content={i18n._(t`Edit User`)} position="top">
                    <ListActionButton
                      variant="plain"
                      component={Link}
                      to={`/users/${user.id}/edit`}
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
export default withI18n()(UserListItem);
