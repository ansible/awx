import React from 'react';
import { shape, number, string, bool, func } from 'prop-types';

import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';
import { Switch } from '@patternfly/react-core';
import { Tr, Td } from '@patternfly/react-table';
import { ActionsTd, ActionItem } from '../PaginatedTable';

function NotificationListItem({
  canToggleNotifications,
  notification,
  detailUrl,
  approvalsTurnedOn,
  startedTurnedOn,
  successTurnedOn,
  errorTurnedOn,
  toggleNotification,

  typeLabels,
  showApprovalsToggle,
}) {
  return (
    <Tr
      id={`notification-row-${notification.id}`}
      ouiaId={`notification-row-${notification.id}`}
    >
      <Td id={`notification-${notification.id}`} dataLabel={t`Name`}>
        <Link to={`${detailUrl}`}>
          <b>{notification.name}</b>
        </Link>
      </Td>
      <Td dataLabel={t`Type`}>{typeLabels[notification.notification_type]}</Td>
      <ActionsTd dataLabel={t`Options`} gridColumns="120px 120px 120px 120px">
        <ActionItem visible={showApprovalsToggle}>
          <Switch
            id={`notification-${notification.id}-approvals-toggle`}
            ouiaId={`notification-${notification.id}-approvals-toggle`}
            label={t`Approval`}
            labelOff={t`Approval`}
            isChecked={approvalsTurnedOn}
            isDisabled={!canToggleNotifications}
            onChange={() =>
              toggleNotification(
                notification.id,
                approvalsTurnedOn,
                'approvals'
              )
            }
            aria-label={t`Toggle notification approvals`}
          />
        </ActionItem>
        <ActionItem visible>
          <Switch
            id={`notification-${notification.id}-started-toggle`}
            ouiaId={`notification-${notification.id}-started-toggle`}
            label={t`Start`}
            labelOff={t`Start`}
            isChecked={startedTurnedOn}
            isDisabled={!canToggleNotifications}
            onChange={() =>
              toggleNotification(notification.id, startedTurnedOn, 'started')
            }
            aria-label={t`Toggle notification start`}
          />
        </ActionItem>
        <ActionItem visible>
          <Switch
            id={`notification-${notification.id}-success-toggle`}
            ouiaId={`notification-${notification.id}-success-toggle`}
            label={t`Success`}
            labelOff={t`Success`}
            isChecked={successTurnedOn}
            isDisabled={!canToggleNotifications}
            onChange={() =>
              toggleNotification(notification.id, successTurnedOn, 'success')
            }
            aria-label={t`Toggle notification success`}
          />
        </ActionItem>
        <ActionItem visible>
          <Switch
            id={`notification-${notification.id}-error-toggle`}
            ouiaId={`notification-${notification.id}-error-toggle`}
            label={t`Failure`}
            labelOff={t`Failure`}
            isChecked={errorTurnedOn}
            isDisabled={!canToggleNotifications}
            onChange={() =>
              toggleNotification(notification.id, errorTurnedOn, 'error')
            }
            aria-label={t`Toggle notification failure`}
          />
        </ActionItem>
      </ActionsTd>
    </Tr>
  );
}

NotificationListItem.propTypes = {
  notification: shape({
    id: number.isRequired,
    name: string.isRequired,
    notification_type: string.isRequired,
  }).isRequired,
  canToggleNotifications: bool.isRequired,
  detailUrl: string.isRequired,
  approvalsTurnedOn: bool,
  errorTurnedOn: bool,
  startedTurnedOn: bool,
  successTurnedOn: bool,
  toggleNotification: func.isRequired,
  typeLabels: shape().isRequired,
  showApprovalsToggle: bool,
};

NotificationListItem.defaultProps = {
  approvalsTurnedOn: false,
  errorTurnedOn: false,
  startedTurnedOn: false,
  successTurnedOn: false,
  showApprovalsToggle: false,
};

export default NotificationListItem;
