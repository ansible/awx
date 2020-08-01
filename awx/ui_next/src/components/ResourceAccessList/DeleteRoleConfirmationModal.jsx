import React, { Fragment } from 'react';
import { func, string } from 'prop-types';
import { Button } from '@patternfly/react-core';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import AlertModal from '../AlertModal';
import { Role } from '../../types';

class DeleteRoleConfirmationModal extends React.Component {
  static propTypes = {
    role: Role.isRequired,
    username: string,
    onCancel: func.isRequired,
    onConfirm: func.isRequired,
  };

  static defaultProps = {
    username: '',
  };

  isTeamRole() {
    const { role } = this.props;
    return typeof role.team_id !== 'undefined';
  }

  render() {
    const { role, username, onCancel, onConfirm, i18n } = this.props;
    const title = i18n._(
      t`Remove ${this.isTeamRole() ? i18n._(t`Team`) : i18n._(t`User`)} Access`
    );
    return (
      <AlertModal
        variant="danger"
        title={title}
        isOpen
        onClose={onCancel}
        actions={[
          <Button
            key="delete"
            variant="danger"
            aria-label={i18n._(t`Confirm delete`)}
            onClick={onConfirm}
          >
            {i18n._(t`Delete`)}
          </Button>,
          <Button key="cancel" variant="secondary" onClick={onCancel}>
            {i18n._(t`Cancel`)}
          </Button>,
        ]}
      >
        {this.isTeamRole() ? (
          <Fragment>
            {i18n._(
              t`Are you sure you want to remove ${role.name} access from ${role.team_name}?  Doing so affects all members of the team.`
            )}
            <br />
            <br />
            {i18n._(
              t`If you only want to remove access for this particular user, please remove them from the team.`
            )}
          </Fragment>
        ) : (
          <Fragment>
            {i18n._(
              t`Are you sure you want to remove ${role.name} access from ${username}?`
            )}
          </Fragment>
        )}
      </AlertModal>
    );
  }
}

export default withI18n()(DeleteRoleConfirmationModal);
