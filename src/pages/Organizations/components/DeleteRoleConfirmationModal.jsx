import React from 'react';
import { func, string } from 'prop-types';
import { Button } from '@patternfly/react-core';
import { I18n, i18nMark } from '@lingui/react';
import { t, Trans } from '@lingui/macro';
import AlertModal from '../../../components/AlertModal';
import { Role } from '../../../types';

class DeleteRoleConfirmationModal extends React.Component {
  static propTypes = {
    role: Role.isRequired,
    username: string,
    onCancel: func.isRequired,
    onConfirm: func.isRequired,
  }

  static defaultProps = {
    username: '',
  }

  isTeamRole () {
    const { role } = this.props;
    return typeof role.team_id !== 'undefined';
  }

  render () {
    const { role, username, onCancel, onConfirm } = this.props;
    const title = `Remove ${this.isTeamRole() ? 'Team' : 'User'} Access`;
    return (
      <I18n>
        {({ i18n }) => (
          <AlertModal
            variant="danger"
            title={i18nMark(title)}
            isOpen
            onClose={this.hideWarning}
            actions={[
              <Button
                key="delete"
                variant="danger"
                aria-label="Confirm delete"
                onClick={onConfirm}
              >
                {i18n._(t`Delete`)}
              </Button>,
              <Button key="cancel" variant="secondary" onClick={onCancel}>
                {i18n._(t`Cancel`)}
              </Button>
            ]}
          >
            {this.isTeamRole() ? (
              <Trans>
                Are you sure you want to remove
                <b>{` ${role.name} `}</b>
                access from
                <b>{` ${role.team_name}`}</b>
                ?  Doing so affects all members of the team.
                <br />
                <br />
                If you
                <b><i> only </i></b>
                want to remove access for this particular user, please remove them from the team.
              </Trans>
            ) : (
              <Trans>
                Are you sure you want to remove
                <b>{` ${role.name} `}</b>
                access from
                <b>{` ${username}`}</b>
                ?
              </Trans>
            )}
          </AlertModal>
        )}
      </I18n>
    );
  }
}

export default DeleteRoleConfirmationModal;
